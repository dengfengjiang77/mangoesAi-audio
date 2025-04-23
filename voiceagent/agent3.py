import logging
import os
import torch
from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, JobProcess, WorkerOptions, cli, llm
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import openai, deepgram, silero, elevenlabs
from transformers import pipeline
from transformers.pipelines.audio_utils import ffmpeg_microphone_live
import asyncio

load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("voice-agent")

from transformers import AutoModelForAudioClassification, AutoProcessor

# 下载模型和处理器
AutoModelForAudioClassification.from_pretrained("MIT/ast-finetuned-speech-commands-v2")
AutoProcessor.from_pretrained("MIT/ast-finetuned-speech-commands-v2")
print("Model and processor downloaded successfully.")



def wake_up(wake_word="marvin", prob_threshold=0.5, chunk_length_s=2.0, stream_chunk_s=0.25, timeout=30):
    """Listen for wake word and return True when detected."""
    logger.info("Initializing wake word detection...")
    
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    classifier = pipeline(
        "audio-classification", 
        model="MIT/ast-finetuned-speech-commands-v2", 
        device=device
    )

    # 检查唤醒词是否有效
    if wake_word not in classifier.model.config.label2id.keys():
        raise ValueError(
            f"Wake word {wake_word} not in valid labels. Choose from: {classifier.model.config.label2id.keys()}"
        )

    sampling_rate = classifier.feature_extractor.sampling_rate
    mic = ffmpeg_microphone_live(
        sampling_rate=sampling_rate,
        chunk_length_s=chunk_length_s,
        stream_chunk_s=stream_chunk_s,
    )

    logger.info(f"Listening for wake word: {wake_word} (timeout: {timeout}s)")
    start_time = time.time()
    for prediction in classifier(mic):
        prediction = prediction[0]
        logger.debug(f"Prediction: {prediction}")
        if prediction["label"] == wake_word and prediction["score"] > prob_threshold:
            logger.info(f"Wake word '{wake_word}' detected!")
            return True
        if time.time() - start_time > timeout:
            logger.warning("Wake word detection timed out.")
            return False


def prewarm(proc: JobProcess):
    """Prepares the environment before the job starts."""
    proc.userdata["vad"] = silero.VAD.load()
    # Store both user and agent transcripts in a dictionary
    proc.userdata["transcripts"] = {
        "user": [],
        "agent": []
    }

async def entrypoint(ctx: JobContext):
    """Main entrypoint for the voice agent."""
    logger.info("Initializing wake word detection...")
    # 唤醒检测
    if not await wake_up(timeout=30):
        logger.info("Wake word not detected. Exiting...")
        return

    logger.info("Wake word detected! Starting conversation...")
    # 连接到房间
    room_name = "test-room"
    logger.info(f"Connecting to room: {room_name}")
    #logger.info(f"Connecting to room {ctx.room.name}")
    await ctx.connect(room_name=room_name, auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for the first participant to connect
    participant = await ctx.wait_for_participant()
    logger.info(f"Participant {participant.identity} joined the room.")

    CARTESIA_API_KEY="sk_25b1248a7ece2bead68d96845024d215e06a5ca8035b82ca"


    # 初始化语音助手
    initial_ctx = llm.ChatContext().append(
        role="system",
        text="You are a voice assistant created by LiveKit. Your interface with users will be voice."
    )
    # Initialize the assistant with VAD, STT, LLM, and TTS capabilities
    assistant = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=deepgram.STT(),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=elevenlabs.TTS(),
        chat_ctx=initial_ctx,
    )

    def on_user_transcript(transcript: str, **kwargs):
        """Handles user STT transcriptions."""
        logger.info(f"User said: {transcript}")
        ctx.proc.userdata["transcripts"]["user"].append(transcript)
        logger.info(f"Current User Transcripts: {ctx.proc.userdata['transcripts']['user']}")

    # This callback might be available in the VoicePipelineAgent.
    # If not, you will need to integrate it at a point where the agent produces the response.
    def on_agent_transcript(transcript: str, **kwargs):
        """Handles agent responses."""
        logger.info(f"Agent said: {transcript}")
        ctx.proc.userdata["transcripts"]["agent"].append(transcript)
        logger.info(f"Current Agent Transcripts: {ctx.proc.userdata['transcripts']['agent']}")

    # Attach the handlers to the assistant
    assistant.on_user_transcript = on_user_transcript
    assistant.on_agent_transcript = on_agent_transcript  # Only if VoicePipelineAgent supports this

    assistant.start(ctx.room, participant)

    async def on_participant_disconnected():
        """Handles participant disconnection and saves STT transcripts."""
        logger.info(f"Participant {participant.identity} has disconnected.")
        save_transcripts_to_file(ctx.proc.userdata["transcripts"])

    participant.on_disconnected = on_participant_disconnected  # Attach the disconnect event

    try:
        logger.info("Running assistant. Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(10)  # Keeps the assistant running to detect disconnections
    except KeyboardInterrupt:
        logger.info("User pressed Ctrl+C. Shutting down.")
    finally:
        logger.info("Reached finally block, attempting to save transcripts...")
        save_transcripts_to_file(ctx.proc.userdata["transcripts"])


def save_transcripts_to_file(transcripts):
    """Saves the captured STT transcriptions from both user and agent to a file."""
    output_dir = "/Users/7one/Documents/Work/mangoesai/voiceagent"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "stt_transcripts.txt")

    logger.info(f"Attempting to save {len(transcripts['user']) + len(transcripts['agent'])} transcriptions to {output_file}")
    logger.info(f"User Transcripts Content: {transcripts['user']}")
    logger.info(f"Agent Transcripts Content: {transcripts['agent']}")

    try:
        with open(output_file, "w", encoding="utf-8") as file:
            file.write("=== User Transcripts ===\n")
            for i, line in enumerate(transcripts["user"], start=1):
                file.write(f"User {i}: {line}\n")

            file.write("\n=== Agent Transcripts ===\n")
            for i, line in enumerate(transcripts["agent"], start=1):
                file.write(f"Agent {i}: {line}\n")

        logger.info(f"Transcriptions saved successfully to {output_file}")
    except Exception as e:
        logger.error(f"Failed to save transcriptions to {output_file}: {e}")


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )
