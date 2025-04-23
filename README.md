# MediSync AI: A Multi-Modal Framework for Structured Information Extraction from Group Therapy Conversations

---

## Key Features

### Feature 1 - Voice Registration
- **Model used**: SpeechBrain  
- **Procedure**:  
  1. Register the user's voice (3~6s voice is needed).  
  2. Verify the voice:  
     - Capture the real-time voice.  
     - Load the voice.  
     - Verify with scores.  
     - Return the result.  

---

### Feature 2 - Training
In this code, we fine-tune the MIT Speech Commands V2 dataset and add the wakeup word "Hey ZZX" to the model. This allows the model to recognize new wakeup words.

#### Procedure:
1. Generate a new voice dataset (at least 30 samples in different voices).  
   - You can use text-to-speech tools to generate:  
     - [Narakeet](https://www.narakeet.com/languages/chinese-text-to-speech)  
     - [MicMonster](https://micmonster.com/text-to-speech/chinese-mandarin-simplified/)  
2. Convert the voices to the required format:  
   - WAV files, 16kHz voice (use provided code).  
3. Split the dataset:  
   - Training dataset (80%) and test dataset (20%).  
   - If you have more data, create a validation dataset as well.  
4. Generate two CSV files (train and test) with the dataset file paths.  
5. Start training and save the model to the local PC.  
6. Perform real-time testing.

---

## Next Steps

- Try to connect with an LLM (Large Language Model) and respond with voice (TTS).
