import requests
import json
import os
import logging
from datetime import datetime
import sqlite3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("health_processor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("health_processor")

api_key = "sk-21d71559fcff455abca426ab396f295b"

class DeepSeekClient:
    def __init__(self, api_key=None, mock_mode=False):
        """Initialize DeepSeek API client"""
        self.api_key = api_key or os.environ.get("api_key")
        self.mock_mode = mock_mode
        
        if not self.api_key and not self.mock_mode:
            raise ValueError("DeepSeek API key is required when not in mock mode")
        
        self.base_url = "https://api.deepseek.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def extract_health_information(self, conversation_text, prompt_template):
        """
        Extract health information from conversation using DeepSeek API
        
        Args:
            conversation_text: The formatted conversation text
            prompt_template: The prompt template to use
            
        Returns:
            Structured health information
        """
        # If mock mode is enabled, return mock data
        if self.mock_mode:
            logger.info("Mock mode enabled, returning mock data")
            
            # Return different mock data based on different prompt templates
            if "general_therapy_extraction" in prompt_template:
                return {
                    "session_summary": "This session focused on emotional expression and coping strategies.",
                    "group_dynamics": "Participants showed support for each other's challenges.",
                    "speakers": [
                        {
                            "speaker_id": "SPEAKER_00",
                            "primary_concerns": ["emotional disconnection", "depression"],
                            "emotions_expressed": ["emptiness", "frustration"],
                            "relationship_dynamics": "Difficulty communicating emotional needs with spouse",
                            "self_perception": "Sees self as emotionally unavailable",
                            "challenges": ["expressing emotions", "connecting with others"],
                            "coping_mechanisms": ["distraction through work", "medication"],
                            "notable_quotes": ["I don't even know what I'm feeling half the time. It's just this emptiness."]
                        },
                        {
                            "speaker_id": "SPEAKER_01",
                            "primary_concerns": ["facilitating group discussion"],
                            "emotions_expressed": ["empathy", "curiosity"],
                            "relationship_dynamics": "Supportive of all group members",
                            "self_perception": None,
                            "challenges": None,
                            "coping_mechanisms": None,
                            "notable_quotes": ["What do you notice in your body when you're feeling this way?"]
                        }
                    ]
                }
            elif "relational_dynamics" in prompt_template:
                return {
                    "group_dynamics_summary": "The group shows a pattern of mutual support with the facilitator guiding discussions.",
                    "facilitator_role": "The facilitator creates a safe space and redirects conversations when needed.",
                    "power_dynamics": [
                        {
                            "description": "The facilitator directs the flow of conversation",
                            "speakers_involved": ["SPEAKER_01", "SPEAKER_02"]
                        }
                    ],
                    "alliances": [
                        {
                            "speakers": ["SPEAKER_02", "SPEAKER_03"],
                            "nature": "Shared experience of feeling overwhelmed"
                        }
                    ],
                    "communication_patterns": "Speaker 01 tends to ask questions while others share personal experiences.",
                    "external_relationships": [
                        {
                            "speaker_id": "SPEAKER_00",
                            "relationship": "Marriage with communication difficulties",
                            "impact": "Creates feelings of isolation and inadequacy"
                        }
                    ]
                }
            elif "therapeutic_progress" in prompt_template:
                return {
                    "session_progress_summary": "The session showed several moments of insight and vulnerability.",
                    "key_insights": [
                        {
                            "speaker_id": "SPEAKER_04",
                            "insight": "Recognition of using work to avoid emotional processing",
                            "significance": "First step toward addressing avoidance patterns"
                        }
                    ],
                    "resistance_areas": [
                        {
                            "speaker_id": "SPEAKER_00",
                            "description": "Difficulty engaging with emotional content",
                            "possible_approach": "Continued gentle exploration of physical sensations of emotions"
                        }
                    ],
                    "effective_interventions": [
                        {
                            "intervener_id": "SPEAKER_01",
                            "intervention": "Normalizing difficult thoughts",
                            "impact": "Reduced shame around uncomfortable thoughts"
                        }
                    ],
                    "progress_indicators": [
                        {
                            "speaker_id": "SPEAKER_02",
                            "area": "Self-compassion",
                            "evidence": "Attempting to challenge negative self-talk"
                        }
                    ],
                    "suggested_focus_areas": [
                        {
                            "speaker_id": "SPEAKER_03",
                            "area": "Work-life balance",
                            "rationale": "Anxiety tied strongly to productivity and work identity"
                        }
                    ]
                }
            else:
                # Default mock response
                return {
                    "mock_response": "This is a mock response",
                    "prompt_type": "unknown"
                }
        
        # Construct the full prompt
        full_prompt = prompt_template.format(conversation=conversation_text)
        
        # Enhance prompt template to ensure JSON response
        full_prompt += "\n\nIMPORTANT: Please ensure your response is a valid JSON object. Do not include any text before or after the JSON."
        
        # Prepare the request payload
        payload = {
            "model": "deepseek-chat",  # Use the appropriate model name
            "messages": [
                {"role": "system", "content": "You are a medical information extraction assistant that always responds with valid JSON."},
                {"role": "user", "content": full_prompt}
            ],
            "temperature": 0.1,  # Low temperature for more deterministic outputs
            "max_tokens": 4000
        }
        
        # Log the request (without sensitive information)
        logger.info(f"Sending request to DeepSeek API with prompt length: {len(full_prompt)}")
        
        try:
            # Make the API call with timeout
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=120  # Increase timeout to 120 seconds
            )
            
            # Parse and return the response
            if response.status_code == 200:
                result = response.json()
                extracted_info = result["choices"][0]["message"]["content"]
                
                # Log original response for debugging
                logger.debug(f"API raw response: {extracted_info[:100]}...")
                
                # Try to clean the response to extract JSON
                clean_response = extracted_info.strip()
                if clean_response.startswith("```json"):
                    clean_response = clean_response[7:]
                if clean_response.endswith("```"):
                    clean_response = clean_response[:-3]
                clean_response = clean_response.strip()
                
                # Try to parse as JSON
                try:
                    if clean_response.startswith("{") and clean_response.endswith("}"):
                        json_response = json.loads(clean_response)
                        return json_response
                    else:
                        logger.warning(f"Response doesn't look like JSON: {clean_response[:50]}...")
                        return clean_response
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse response as JSON: {e}")
                    # Save original response for debugging
                    with open(f"failed_json_response_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt", "w") as f:
                        f.write(extracted_info)
                    return clean_response
            else:
                error_msg = f"API request failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            logger.exception("Error calling DeepSeek API")
            raise

def prepare_therapy_conversation(raw_diarization):
    """
    Prepare the therapy group diarization for DeepSeek API
    
    Args:
        raw_diarization: Raw diarization output as a string
        
    Returns:
        Formatted conversation text and speaker mapping
    """
    # First, we need to parse the raw diarization into a more structured format
    lines = raw_diarization.strip().split("SPEAKER_")
    
    # Remove empty lines
    lines = [line.strip() for line in lines if line.strip()]
    
    # Process each line
    formatted_lines = []
    speaker_ids = set()
    
    for line in lines:
        # Extract speaker ID and text
        parts = line.split(":", 1)
        if len(parts) == 2:
            speaker_id = parts[0].strip()
            text = parts[1].strip()
            
            # Map numeric speaker IDs to proper format
            full_speaker_id = f"SPEAKER_{speaker_id}" if speaker_id.isdigit() else speaker_id
            speaker_ids.add(full_speaker_id)
            
            formatted_lines.append(f"{full_speaker_id}: {text}")
    
    # Join formatted lines
    formatted_conversation = "\n".join(formatted_lines)
    
    # Create speaker mapping (for reference)
    speaker_mapping = {speaker_id: f"Person_{i+1}" for i, speaker_id in enumerate(sorted(speaker_ids))}
    
    return formatted_conversation, speaker_mapping

class TherapyPromptTemplates:
    @staticmethod
    def get_general_therapy_extraction_prompt():
        return """
        I have a transcript from a group therapy session. Please analyze this conversation and extract key mental health and emotional information in a structured JSON format.
        
        Conversation transcript:
        {conversation}
        
        Please extract the following information for each speaker:
        1. Emotions expressed
        2. Mental health concerns mentioned or implied
        3. Relationship issues discussed
        4. Self-perception issues
        5. Key challenges or struggles
        6. Coping mechanisms mentioned
        
        Format your response as a valid JSON object with the following structure:
        {{
            "session_summary": "Brief summary of the overall session",
            "group_dynamics": "Brief description of how participants interact",
            "speakers": [
                {{
                    "speaker_id": "Speaker ID",
                    "primary_concerns": ["concern1", "concern2", ...],
                    "emotions_expressed": ["emotion1", "emotion2", ...],
                    "relationship_dynamics": "Description of relationship issues",
                    "self_perception": "Description of self-perception issues",
                    "challenges": ["challenge1", "challenge2", ...],
                    "coping_mechanisms": ["mechanism1", "mechanism2", ...],
                    "notable_quotes": ["quote1", "quote2", ...]
                }},
                ...
            ]
        }}
        
        Important guidelines:
        - Only include information explicitly stated in the conversation
        - Avoid making diagnostic statements or clinical judgments
        - If information is unclear or not mentioned, use null values
        - Focus on emotional content and interpersonal dynamics
        - Identify any potential safety concerns (suicidal ideation, abuse, etc.)
        """
    
    @staticmethod
    def get_relational_dynamics_prompt():
        return """
        I have a transcript from a group therapy session. Please focus specifically on analyzing the relational dynamics between participants.
        
        Conversation transcript:
        {conversation}
        
        Please extract and analyze:
        1. Power dynamics in the group
        2. Alliance patterns (who supports whom)
        3. Communication patterns (who speaks to whom, who interrupts)
        4. Emotional reactions between participants
        5. Mentioned relationships outside the group
        
        Format your response as a valid JSON object with the following structure:
        {{
            "group_dynamics_summary": "Overall analysis of group dynamics",
            "facilitator_role": "Analysis of how the facilitator/therapist functions",
            "power_dynamics": [
                {{
                    "description": "Description of a power dynamic",
                    "speakers_involved": ["SPEAKER_ID1", "SPEAKER_ID2"]
                }},
                ...
            ],
            "alliances": [
                {{
                    "speakers": ["SPEAKER_ID1", "SPEAKER_ID2"],
                    "nature": "Description of alliance"
                }},
                ...
            ],
            "communication_patterns": "Analysis of who speaks to whom",
            "external_relationships": [
                {{
                    "speaker_id": "SPEAKER_ID",
                    "relationship": "Description of external relationship",
                    "impact": "How this affects the speaker"
                }},
                ...
            ]
        }}
        """
    
    @staticmethod
    def get_therapeutic_progress_prompt():
        return """
        I have a transcript from a group therapy session. Please analyze this conversation for signs of therapeutic progress, insights, and areas that may need further attention.
        
        Conversation transcript:
        {conversation}
        
        Please extract and analyze:
        1. Moments of insight or breakthrough
        2. Areas of resistance or avoidance
        3. Therapeutic interventions and their effectiveness
        4. Evidence of progress in addressing issues
        5. Areas that may need further therapeutic attention
        
        Format your response as a valid JSON object with the following structure:
        {{
            "session_progress_summary": "Overall assessment of progress in this session",
            "key_insights": [
                {{
                    "speaker_id": "SPEAKER_ID",
                    "insight": "Description of insight",
                    "significance": "Why this insight matters"
                }},
                ...
            ],
            "resistance_areas": [
                {{
                    "speaker_id": "SPEAKER_ID",
                    "description": "Description of resistance",
                    "possible_approach": "Suggestion for addressing"
                }},
                ...
            ],
            "effective_interventions": [
                {{
                    "intervener_id": "SPEAKER_ID of therapist/member",
                    "intervention": "Description of intervention",
                    "impact": "Observed impact"
                }},
                ...
            ],
            "progress_indicators": [
                {{
                    "speaker_id": "SPEAKER_ID",
                    "area": "Area of progress",
                    "evidence": "Evidence from transcript"
                }},
                ...
            ],
            "suggested_focus_areas": [
                {{
                    "speaker_id": "SPEAKER_ID",
                    "area": "Area needing attention",
                    "rationale": "Why this needs attention"
                }},
                ...
            ]
        }}
        """

class TherapyDataProcessor:
    def __init__(self, api_key=None):
        """Initialize the therapy data processor"""
        self.deepseek_client = DeepSeekClient(api_key)
        self.prompt_templates = TherapyPromptTemplates()
    
    def process_conversation(self, raw_diarization):
        """
        Process a therapy group diarization and extract structured information
        
        Args:
            raw_diarization: Raw diarization output as a string
            
        Returns:
            Dictionary with extracted information
        """
        # Prepare the conversation data
        conversation_text, speaker_mapping = prepare_therapy_conversation(raw_diarization)
        
        # Log the conversation processing
        logger.info(f"Processing conversation with {len(speaker_mapping)} speakers")
        
        # Create a session ID
        session_id = f"therapy_session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        try:
            # Extract general therapeutic information
            logger.info("Extracting general therapeutic information")
            general_prompt = self.prompt_templates.get_general_therapy_extraction_prompt()
            general_info = self.deepseek_client.extract_health_information(
                conversation_text, general_prompt
            )
            
            # Extract relational dynamics information
            logger.info("Extracting relational dynamics information")
            relational_prompt = self.prompt_templates.get_relational_dynamics_prompt()
            relational_info = self.deepseek_client.extract_health_information(
                conversation_text, relational_prompt
            )
            
            # Extract therapeutic progress information
            logger.info("Extracting therapeutic progress information")
            progress_prompt = self.prompt_templates.get_therapeutic_progress_prompt()
            progress_info = self.deepseek_client.extract_health_information(
                conversation_text, progress_prompt
            )
            
            # Combine all extracted information
            combined_info = self._combine_extracted_info(
                session_id, 
                general_info, 
                relational_info, 
                progress_info,
                speaker_mapping
            )
            
            return combined_info
            
        except Exception as e:
            logger.exception("Error processing conversation")
            raise
    
    def _combine_extracted_info(self, session_id, general_info, relational_info, progress_info, speaker_mapping):
        """
        Combine information from different extraction prompts
        
        Args:
            session_id: The session ID
            general_info: General therapeutic information
            relational_info: Relational dynamics information
            progress_info: Therapeutic progress information
            speaker_mapping: Mapping of speaker IDs to more readable names
            
        Returns:
            Combined therapeutic information
        """
        # Create default information structures
        default_general_info = {
            "session_summary": "",
            "group_dynamics": "",
            "speakers": []
        }
        
        default_relational_info = {
            "group_dynamics_summary": "",
            "facilitator_role": "",
            "power_dynamics": [],
            "alliances": [],
            "communication_patterns": "",
            "external_relationships": []
        }
        
        default_progress_info = {
            "session_progress_summary": "",
            "key_insights": [],
            "resistance_areas": [],
            "effective_interventions": [],
            "progress_indicators": [],
            "suggested_focus_areas": []
        }
        
        # Try to parse strings as JSON
        if isinstance(general_info, str):
            try:
                general_info = json.loads(general_info)
            except json.JSONDecodeError:
                logger.warning("Failed to parse general_info as JSON")
                # Save original response for debugging
                with open("general_info_response.txt", "w") as f:
                    f.write(general_info)
                general_info = default_general_info
        
        if isinstance(relational_info, str):
            try:
                relational_info = json.loads(relational_info)
            except json.JSONDecodeError:
                logger.warning("Failed to parse relational_info as JSON")
                # Save original response for debugging
                with open("relational_info_response.txt", "w") as f:
                    f.write(relational_info)
                relational_info = default_relational_info
        
        if isinstance(progress_info, str):
            try:
                progress_info = json.loads(progress_info)
            except json.JSONDecodeError:
                logger.warning("Failed to parse progress_info as JSON")
                # Save original response for debugging
                with open("progress_info_response.txt", "w") as f:
                    f.write(progress_info)
                progress_info = default_progress_info
        
        # Create combined information structure
        combined_info = {
            "session_id": session_id,
            "session_date": datetime.now().isoformat(),
            "session_summary": general_info.get("session_summary", ""),
            "group_dynamics": general_info.get("group_dynamics", ""),
            "relational_dynamics_summary": relational_info.get("group_dynamics_summary", ""),
            "facilitator_assessment": relational_info.get("facilitator_role", ""),
            "session_progress_summary": progress_info.get("session_progress_summary", ""),
            "speaker_mapping": speaker_mapping,
            "speakers": [],
            "raw_responses": {
                "general_info_type": type(general_info).__name__,
                "relational_info_type": type(relational_info).__name__,
                "progress_info_type": type(progress_info).__name__
            }
        }
        
        # Get all unique speaker IDs
        all_speaker_ids = set()
        for info in [general_info, relational_info, progress_info]:
            speakers = info.get("speakers", [])
            for speaker in speakers:
                if "speaker_id" in speaker:
                    all_speaker_ids.add(speaker["speaker_id"])
        
        # If no speakers found, use speaker_mapping IDs
        if not all_speaker_ids and speaker_mapping:
            all_speaker_ids = set(speaker_mapping.keys())
        
        # Add speakers from progress_info
        for key in ["key_insights", "resistance_areas", "progress_indicators", "suggested_focus_areas"]:
            if key in progress_info:
                for item in progress_info[key]:
                    if "speaker_id" in item:
                        all_speaker_ids.add(item["speaker_id"])
        
        # Combine information for each speaker
        for speaker_id in all_speaker_ids:
            speaker_info = {"speaker_id": speaker_id}
            
            # Add basic information
            for speaker in general_info.get("speakers", []):
                if speaker.get("speaker_id") == speaker_id:
                    for key, value in speaker.items():
                        if key != "speaker_id":
                            speaker_info[key] = value
            
            # Add insights information
            speaker_info["insights"] = []
            for insight in progress_info.get("key_insights", []):
                if insight.get("speaker_id") == speaker_id:
                    speaker_info["insights"].append({
                        "insight": insight.get("insight", ""),
                        "significance": insight.get("significance", "")
                    })
            
            # Add resistance areas
            speaker_info["resistance_areas"] = []
            for resistance in progress_info.get("resistance_areas", []):
                if resistance.get("speaker_id") == speaker_id:
                    speaker_info["resistance_areas"].append({
                        "description": resistance.get("description", ""),
                        "possible_approach": resistance.get("possible_approach", "")
                    })
            
            # Add progress indicators
            speaker_info["progress_indicators"] = []
            for progress in progress_info.get("progress_indicators", []):
                if progress.get("speaker_id") == speaker_id:
                    speaker_info["progress_indicators"].append({
                        "area": progress.get("area", ""),
                        "evidence": progress.get("evidence", "")
                    })
            
            # Add suggested focus areas
            speaker_info["suggested_focus_areas"] = []
            for focus in progress_info.get("suggested_focus_areas", []):
                if focus.get("speaker_id") == speaker_id:
                    speaker_info["suggested_focus_areas"].append({
                        "area": focus.get("area", ""),
                        "rationale": focus.get("rationale", "")
                    })
            
            # Add external relationships
            speaker_info["external_relationships"] = []
            for relationship in relational_info.get("external_relationships", []):
                if relationship.get("speaker_id") == speaker_id:
                    speaker_info["external_relationships"].append({
                        "relationship": relationship.get("relationship", ""),
                        "impact": relationship.get("impact", "")
                    })
            
            combined_info["speakers"].append(speaker_info)
        
        # Add group dynamics information
        combined_info["power_dynamics"] = relational_info.get("power_dynamics", [])
        combined_info["alliances"] = relational_info.get("alliances", [])
        combined_info["communication_patterns"] = relational_info.get("communication_patterns", "")
        combined_info["effective_interventions"] = progress_info.get("effective_interventions", [])
        
        return combined_info

class TherapyRecordStorage:
    def __init__(self, db_path="therapy_records.db"):
        """Initialize therapy record storage"""
        self.db_path = db_path
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize the database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create sessions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS therapy_sessions (
            session_id TEXT PRIMARY KEY,
            session_date TEXT,
            session_summary TEXT,
            group_dynamics TEXT,
            facilitator_assessment TEXT,
            session_progress_summary TEXT,
            created_at TEXT,
            raw_data TEXT
        )
        ''')
        
        # Create speakers table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS therapy_participants (
            speaker_id TEXT,
            session_id TEXT,
            participant_data TEXT,
            PRIMARY KEY (speaker_id, session_id),
            FOREIGN KEY (session_id) REFERENCES therapy_sessions(session_id)
        )
        ''')
        
        # Create group dynamics table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS group_dynamics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            dynamic_type TEXT,
            dynamic_data TEXT,
            FOREIGN KEY (session_id) REFERENCES therapy_sessions(session_id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_therapy_record(self, processed_data):
        """
        Save processed therapy record to database
        
        Args:
            processed_data: Combined therapy information
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Extract session information
            session_id = processed_data.get("session_id")
            session_date = processed_data.get("session_date")
            session_summary = processed_data.get("session_summary", "")
            group_dynamics = processed_data.get("group_dynamics", "")
            facilitator_assessment = processed_data.get("facilitator_assessment", "")
            session_progress_summary = processed_data.get("session_progress_summary", "")
            
            # Save session information
            cursor.execute(
                "INSERT OR REPLACE INTO therapy_sessions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    session_id,
                    session_date,
                    session_summary,
                    group_dynamics,
                    facilitator_assessment,
                    session_progress_summary,
                    datetime.now().isoformat(),
                    json.dumps(processed_data)
                )
            )
            
            # Save speaker information
            for speaker in processed_data.get("speakers", []):
                speaker_id = speaker.get("speaker_id", "unknown")
                cursor.execute(
                    "INSERT OR REPLACE INTO therapy_participants VALUES (?, ?, ?)",
                    (
                        speaker_id,
                        session_id,
                        json.dumps(speaker)
                    )
                )
            
            # Save group dynamics
            for dynamic_type in ["power_dynamics", "alliances", "effective_interventions"]:
                for dynamic in processed_data.get(dynamic_type, []):
                    cursor.execute(
                        "INSERT INTO group_dynamics (session_id, dynamic_type, dynamic_data) VALUES (?, ?, ?)",
                        (
                            session_id,
                            dynamic_type,
                            json.dumps(dynamic)
                        )
                    )
            
            conn.commit()
            conn.close()
            return True
        
        except Exception as e:
            logger.error(f"Error saving therapy record: {e}")
            return False

def process_therapy_diarization(raw_diarization, api_key=None):
    """
    Process therapy diarization and save to database
    
    Args:
        raw_diarization: Raw diarization output as a string
        api_key: DeepSeek API key (optional if set in environment)
        
    Returns:
        Dictionary with processing results
    """
    try:
        # Initialize processor and storage
        processor = TherapyDataProcessor(api_key)
        storage = TherapyRecordStorage()
        
        # Process the conversation
        logger.info("Processing therapy conversation with DeepSeek API...")
        processed_data = processor.process_conversation(raw_diarization)
        
        # Save to database
        logger.info("Saving processed therapy data to database...")
        success = storage.save_therapy_record(processed_data)
        
        # Return results
        return {
            "success": success,
            "processed_data": processed_data,
            "session_id": processed_data.get("session_id")
        }
    except Exception as e:
        logger.exception("Failed to process therapy diarization")
        return {
            "success": False,
            "error": str(e)
        }

# Define conversation sample functions, but split long strings into parts
def get_original_therapy_conversation():
    """Return the original therapy conversation sample."""
    return (
        "SPEAKER_02: Any feedback for Gil? Any help for Gil? SPEAKER_02: I'd like to ask, I'd like to tell Gil I feel the same way. I feel a lot of, that I know a lot about how people around you feel. "
        "SPEAKER_01: Even when you share stories from when you were younger. It's always about how people are feeling. SPEAKER_01: And if you could share anything right now that would be about you, that would be, I'm sorry, I'm sorry I'm stuttering. "
        "SPEAKER_01: That would be about you right now to let us in would be great. SPEAKER_01: Vonna you don't need to say I'm sorry every time you have a comment to make. Are you aware that you do that? "
        "SPEAKER_01: Yeah. Yes. I just, I just, I just feel like I'm wrong. SPEAKER_01: You just feel like what? SPEAKER_01: I'm wrong I don't know. SPEAKER_02: Can we flag that and come back to that in a moment because I think that you're onto something really important with Gil. "
        "SPEAKER_02: So I'm going to ask you to push him. Can you do that? SPEAKER_02: I think so. SPEAKER_01: So Gil, in your relationship with Rose, you talk a lot about how she's very controlling and she won't give you a child and she's cold to you. "
        "SPEAKER_01: Is there any reason why you might think that she would act that way? SPEAKER_00: I just, I just still am having a hard time feeling that my, what's going on in my life is all that important Julius. "
        "SPEAKER_00: I can only imagine what you're going through and here I am complaining about a nagging wife and I mean in the end so maybe I don't have a child. "
        "SPEAKER_00: Maybe I'm not supposed to have, maybe I'm not supposed to have a child. SPEAKER_02: What would it be like? Wait a minute. We don't have Rose here. "
        "SPEAKER_02: We only can imagine what Rose is like. SPEAKER_02: So let me ask you this question. Rebecca, Bonnie, Pam, if you were married to Gil based upon what you know of Gil through this group, what would it be like to be his wife? "
        "SPEAKER_02: How would that feel? SPEAKER_01: It would feel like I was outside knocking on a door and then I would have to knock louder and knock harder and do different things in order to get attention. "
        "SPEAKER_02: I was going to say something similar actually. I would feel like I was screaming at a wall trying to get through to you."
    )

def get_comprehensive_therapy_conversation():
    """Return a more comprehensive therapy conversation sample with various emotional and mental health elements."""
    part1 = (
        "SPEAKER_01: Welcome everyone to our group session today. I'd like to check in with each of you about how your week has been. Maya, would you like to start? "
        "SPEAKER_03: I've been feeling really overwhelmed lately with work. The deadline pressure is intense, and I've started having trouble sleeping again. "
        "SPEAKER_03: I wake up at 3 AM almost every night with my heart racing, thinking about all the things I haven't finished. "
        "SPEAKER_03: My partner says I've been irritable and distant. He's trying to be supportive, but I just don't have the energy to connect right now. "
    )
    
    part2 = (
        "SPEAKER_01: Thank you for sharing that, Maya. What do you notice in your body when you're feeling this way? "
        "SPEAKER_03: My shoulders are always tight, and I get these tension headaches. Sometimes I feel like I can't breathe properly. "
        "SPEAKER_03: I've been trying to use that breathing technique we talked about last session, but it's hard to remember when I'm in the middle of panicking. "
        "SPEAKER_02: I can relate to that feeling of being overwhelmed. For me, it's my kids and my parents. I'm stretched so thin trying to care for everyone. "
    )
    
    part3 = (
        "SPEAKER_02: Sometimes I fantasize about just getting in my car and driving away. Not forever, just for a little while to catch my breath. "
        "SPEAKER_02: Then I feel terrible for even thinking that. What kind of mother thinks about leaving? "
        "SPEAKER_01: That sounds like a lot of self-judgment, Sarah. We've talked about how those thoughts are actually quite common and don't reflect on your worth as a parent. "
        "SPEAKER_00: I think I do the opposite. When things get too intense with my emotions, I just shut down. "
    )
    
    part4 = (
        "SPEAKER_00: My wife Rachel keeps telling me that I never share what I'm feeling. She says it's like living with a robot sometimes. "
        "SPEAKER_00: The truth is, I don't even know what I'm feeling half the time. It's just this emptiness. "
        "SPEAKER_01: David, that disconnection from your emotions is something we've been working on. Have you tried that journaling exercise? "
        "SPEAKER_00: I tried a couple times, but it feels pointless. I just stare at the blank page and nothing comes. "
    )
    
    part5 = (
        "SPEAKER_00: It's easier to just focus on work or fixing things around the house. At least then I feel useful. "
        "SPEAKER_04: I've been struggling with that too, David. After my divorce, I threw myself into my job. "
        "SPEAKER_04: But last week, my daughter told me she feels like I don't have time for her anymore. That was a wake-up call. "
        "SPEAKER_04: I realized I've been using work to avoid dealing with my feelings of failure about my marriage ending. "
    )
    
    part6 = (
        "SPEAKER_01: That's an important insight, James. How did it feel to hear that from your daughter? "
        "SPEAKER_04: Horrible. Like I was failing at being a father too. But also... I don't know, maybe grateful? "
        "SPEAKER_04: It forced me to see what I've been doing. I actually took a day off work this week to take her hiking. We talked more than we have in months. "
        "SPEAKER_03: How do you do that though? I feel like if I took a day off, the anxiety would be even worse. "
    )
    
    part7 = (
        "SPEAKER_03: My self-worth is so tied to my productivity. If I'm not working, who am I even? "
        "SPEAKER_02: I've been seeing this therapist individually who suggested I write down negative thoughts and challenge them. "
        "SPEAKER_02: Like when I think \"I'm a bad mother for wanting time alone,\" I try to reframe it as \"I need to care for myself to be present for my children.\" "
        "SPEAKER_02: It helps sometimes, but other times the guilt is just too strong. "
    )
    
    part8 = (
        "SPEAKER_01: Thank you for sharing that technique, Sarah. Maya, does that sound like something that might be helpful for your situation? "
        "SPEAKER_03: Maybe. I just don't see how changing my thoughts fixes the fact that I have too much to do and not enough time. "
        "SPEAKER_00: I tried medication for a while last year. The doctor said I have depression. "
        "SPEAKER_00: It helped a little, but I hated the side effects. I stopped taking it after three months. "
    )
    
    part9 = (
        "SPEAKER_00: Rachel doesn't know I stopped. She thinks I'm still on it. "
        "SPEAKER_01: That sounds like an important piece of information you're keeping from your partner, David. What prevents you from telling her? "
        "SPEAKER_00: She'll be disappointed. She thought the medication was helping our relationship. "
        "SPEAKER_00: And maybe it was. But I felt like a different person on it, not necessarily a better one. "
    )
    
    part10 = (
        "SPEAKER_04: I've found that exercise helps me manage my stress better than anything else. "
        "SPEAKER_04: When I'm running, it's the only time my brain shuts off from all the negative thoughts. "
        "SPEAKER_04: Before the divorce, I'd stopped taking care of myself physically. Getting back to it has been one small positive. "
        "SPEAKER_02: I wish I had time for exercise. Between the kids and my parents' care, I barely have time to shower. "
    )
    
    part11 = (
        "SPEAKER_02: My way of coping has been these little moments of connection with my kids. Like reading them bedtime stories. "
        "SPEAKER_02: For those few minutes, I'm just present and nothing else matters. "
        "SPEAKER_01: These are all important reflections on how you're managing difficult emotions and situations. For our remaining time today, I'd like to focus on one small step each of you might take this week."
    )
    
    return part1 + part2 + part3 + part4 + part5 + part6 + part7 + part8 + part9 + part10 + part11

def get_depression_focused_conversation():
    """Return a therapy conversation focused on depression."""
    part1 = (
        "SPEAKER_01: Today, I'd like to focus our discussion on how everyone has been managing their mood this past week. Let's start with a check-in. "
        "SPEAKER_03: I've been having a really difficult time getting out of bed in the mornings. It takes me at least an hour to convince myself it's worth it. "
        "SPEAKER_03: Everything feels like such an effort. Even showering feels exhausting some days. "
        "SPEAKER_03: My husband keeps telling me to just push through it, but he doesn't understand how heavy everything feels. "
    )
    
    part2 = (
        "SPEAKER_01: That heaviness you're describing is important to acknowledge, Lisa. How long have you been experiencing this level of difficulty? "
        "SPEAKER_03: It's been getting worse over the past month. I think it started after I didn't get that promotion at work. "
        "SPEAKER_03: I keep replaying everything I said in that interview and thinking about how I failed. "
        "SPEAKER_03: I feel like such a disappointment to my family. They were all expecting me to get it. "
    )
    
    part3 = (
        "SPEAKER_00: I understand what you mean about the heaviness. For me, it's like wearing a weighted blanket all the time. "
        "SPEAKER_00: My doctor increased my antidepressant dosage last month, and it's helping a little bit, but the side effects are annoying. "
        "SPEAKER_00: I've gained weight, which honestly just makes me feel worse about myself. "
        "SPEAKER_02: Have you tried any other treatments besides medication? I've been doing this light therapy thing every morning. "
    )
    
    part4 = (
        "SPEAKER_02: My therapist recommended it for seasonal depression. I was skeptical at first, but I do notice a difference when I skip a day. "
        "SPEAKER_02: The hardest part for me is the negative thoughts. I can't seem to stop criticizing myself for every little thing. "
        "SPEAKER_01: That's a good point about alternative treatments. What kinds of things have others tried that have been helpful? "
        "SPEAKER_04: I've been forcing myself to go for a walk every day, even when I don't feel like it. Especially when I don't feel like it. "
    )
    
    # Continue with more parts as needed
    part5 = (
        "SPEAKER_04: The first 10 minutes are always awful, but by the end, I usually feel at least a little better. "
        "SPEAKER_04: My biggest struggle is isolation. I keep canceling plans with friends because it feels too overwhelming to socialize. "
        "SPEAKER_03: I do that too. Then I feel guilty for being a bad friend, which makes me want to isolate more. It's a terrible cycle. "
        "SPEAKER_03: My sister suggested I try journaling, but whenever I sit down to write, I just end up listing all the things that are wrong with me. "
    )
    
    return part1 + part2 + part3 + part4 + part5

def get_anxiety_focused_conversation():
    """Return a therapy conversation focused on anxiety."""
    return (
        "SPEAKER_01: Welcome everyone. Today I thought we could discuss how anxiety has been showing up in your lives this week. Who would like to start? "
        "SPEAKER_02: I had a panic attack in the grocery store on Tuesday. It was so embarrassing. "
        "SPEAKER_02: I was standing in the checkout line and suddenly felt like I couldn't breathe. My heart was racing and I got really dizzy. "
        "SPEAKER_02: I abandoned my cart and just ran out to my car. Sat there for 30 minutes trying to calm down. "
        "SPEAKER_01: That sounds really intense, Karen. What do you think triggered it? "
        "SPEAKER_02: I'm not sure exactly. The store was crowded, and I started worrying that people were looking at me. "
        "SPEAKER_02: Then I started thinking about all the things I needed to do this week, and it just snowballed from there. "
        "SPEAKER_02: I've been avoiding going back since then, which is a problem because we need groceries. "
    )

def get_relationship_focused_conversation():
    """Return a therapy conversation focused on relationship issues."""
    return (
        "SPEAKER_01: Today I'd like us to explore how your mental health affects your relationships, and vice versa. Who would like to begin? "
        "SPEAKER_03: My husband and I have been fighting a lot lately. He says I'm too negative all the time. "
        "SPEAKER_03: I don't think he understands that I can't just \"cheer up\" or \"look on the bright side\" when I'm depressed. "
        "SPEAKER_03: Last night he told me he's tired of walking on eggshells around me. That really hurt. "
        "SPEAKER_01: That sounds painful, Maria. How did you respond when he said that? "
        "SPEAKER_03: I shut down. What could I say? He's not entirely wrong. I know I'm difficult to live with right now. "
        "SPEAKER_03: But hearing him say it out loud made me feel even more worthless and guilty. "
        "SPEAKER_03: Sometimes I think he'd be better off without me dragging him down. "
    )

def get_trauma_focused_conversation():
    """Return a therapy conversation focused on trauma."""
    return (
        "SPEAKER_01: Today, I wanted to create space for us to discuss how trauma has affected your lives and the coping strategies you've developed. Who would like to begin? "
        "SPEAKER_00: I still have nightmares about the car accident. It's been three years, but I wake up in a panic at least twice a week. "
        "SPEAKER_00: Sometimes I'm back in the car, hearing the metal crush. Other times I'm just searching for my daughter in the wreckage. "
        "SPEAKER_00: She wasn't even in the car with me when it happened, but in my dreams, I can't find her and I'm terrified. "
        "SPEAKER_01: Those nightmares sound incredibly distressing. How have they affected your daily life? "
        "SPEAKER_00: I'm exhausted all the time from not sleeping well. And I still can't drive on highways. "
        "SPEAKER_00: My wife has to do all the driving when we travel. I feel ashamed about it, like I should be over this by now. "
        "SPEAKER_00: I've started making excuses to avoid trips that would involve highways, which is affecting my work and family obligations. "
    )

def get_substance_use_conversation():
    """Return a therapy conversation focused on substance use issues."""
    return (
        "SPEAKER_01: Today, I thought we could discuss your relationships with substances - alcohol, medication, or other drugs - and how they impact your mental health. Who would like to start? "
        "SPEAKER_04: I've been sober for 68 days now. The longest stretch I've had in years. "
        "SPEAKER_04: The first month was really hard. I kept having these intense cravings, especially after work when I would usually have a drink. "
        "SPEAKER_04: My anxiety is actually worse without the alcohol. I didn't realize how much I was using it to numb those feelings. "
        "SPEAKER_01: Thank you for sharing that, Michael. 68 days is significant. How are you managing the anxiety now? "
        "SPEAKER_04: I'm trying meditation, but honestly, I'm not very good at it yet. My mind keeps racing. "
        "SPEAKER_04: My sponsor suggested exercise, so I've been going for runs. That helps in the moment, but the anxiety comes back. "
        "SPEAKER_04: My doctor wants me to try medication, but I'm afraid of becoming dependent on something else. "
    )

# Main function
def main():
    """Main function to demonstrate the system"""
    # Choose whether to enable mock mode or actual API call
    mock_mode = False  # Set to True to test without consuming API quota
    
    # Sample conversation data
    sample_diarization = get_comprehensive_therapy_conversation()
    
    # Process conversation data
    if mock_mode:
        # Use mock mode
        processor = TherapyDataProcessor(api_key)
        processor.deepseek_client.mock_mode = True
        processed_data = processor.process_conversation(sample_diarization)
        result = {
            "success": True,
            "processed_data": processed_data,
            "session_id": f"mock_session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }
    else:
        # Use API mode
        result = process_therapy_diarization(sample_diarization, api_key)
    
    # Output results
    if result["success"]:
        print("Processing successful!")
        print(f"Session ID: {result['session_id']}")
        print("Processed Data Sample:")
        print(json.dumps(result["processed_data"], indent=2))
    else:
        print("Processing failed!")
        print(f"Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()