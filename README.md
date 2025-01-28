# mangoesAi-audio
# MangoesAi Playground on several client faced project

# Key Features:

## Feature 1 - Quick Start
### Voice Registration
#### - model used: Speechbrain 
#### - procedure : 
####  - register the user's voice ( 3~6s voice is needed)
####  - verify the voice
####    - capture the real-time voice
####    - load the voice
####    - verify with scores
####    - return result 


Feature 2 - Quick Start

# Training
## In this code, we fine-tune the MIT speech commands V2, add "Hey ZZX" to the model, after that we can use this new model to recognize our new wakeup words
## Procedure:
### - Generate the new voice dataset ( at least 30 samples in different voice), you can use text to speech tools to generate
####  - https://www.narakeet.com/languages/chinese-text-to-speech
####  - https://micmonster.com/text-to-speech/chinese-mandarin-simplified/
### - Covert the voice to required type (wav file, 16kHz voice) - use code
### - Split it to training dataset(80%) and test dataset(20%), if you have more data , leave some validation dataset  - use code
### - generate two csv file(train and test), with their links
### - Start to Train , save the model to local PC
### - Realtime test


# Next Step

## Try to connect with LLM and response with Voice(TTS)