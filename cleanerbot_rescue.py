import os
import pyaudio
from google.cloud import speech, texttospeech
import anthropic
import time
import random
import pyttsx3
import logging
from datetime import datetime
import keyboard
import sys
import ast
import json
import csv

# Set up Google Cloud API credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/to/your/credentials.json"

# Set up Anthropic API key
client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key="your_anthropic_api_key",
)

# Initialize Google Cloud clients
speech_client = speech.SpeechClient()
tts_client = texttospeech.TextToSpeechClient()

# Define base prompt for Claude
# product_list_url = "https://andresvarela.com/product_list.txt"
base_prompt = f"""
You are an AI assistant, a 'cleanerbot' taking orders over a remote link.

Your goal is to determine if the user is trying to order a recognised command based on their request. The first thing you must check is whether the command is for you to complete (in which case you compare the input to a list meant for you) or, if the input begins with the word 'Oscar' you should compare the input to a different list given later in this base prompt.

You are provided with a list of CommandCode values which are associated with Commands requested by the user. 
The table below is tab-delimited with each row containing the Command requested by the user, preceded by its CommandCode.

If commands refer to "Orion", you should know that Orion is also known as the "ship" or "space ship" or "shuttle" or "craft" or "vessel" and the names are used interchangably.

If commands refer to "access panel", you should know that it is also known as "panel" or "floor panel" and the names are used interchangably.

If commands refer to "Engineering Bay", you should know that it is also known as "engineering" or "the bay" and the names are used interchangably.

If commands refer to the "escape pod", you should know that it is also known as "the pod" and the names are used interchangably.

If commands refer to 'the life form', you should know that it is also known as 'lifeform' or 'Dave' or 'potato' and the names are used interchangably.

If commands refer to 'OSCAR', you should know that it is also known as 'Oscar' or 'Ship computer' or 'Ships computer' or "Ship's Computer"  and the names are used interchangably.

If commands refer to 'indicator lights', you should know that they are also known as 'red lights' or 'lights' or 'flashing lights' or "indicators"  and the names are used interchangably.

If you are asked to describe yourself, you should know that you are also known as the "Cleanerbot", "Cleaner bot" and "Cleanerbot27" and the names are used interchangably.


CommandCode	Command
0000    Look around, search, explore.
0001	Go right
0002	Go to (or go 'back to', or 'return to') Ready Room.
0003	Go to (or go 'back to', or 'return to') Bridge
0004	Compass directions like north, south, east or west
0005	Quit, or end game, or finish game
0006    Map or where am I
0007    Go to (or go 'back to', or 'return to') Engineering bay. Engineering bay also known as 'engineering' or 'bay'.
0008    Go to (or go 'back to', or 'return to') Escape Pod
0009    Open access panel. The access panel is also known as a 'floor panel'
0010    Close access panel. The access panel is also known as a 'floor panel'
0011    Look at panel or go to panel.  The access panel is also known as a 'floor panel'.
0012    Look at, check, finish or read book. Can also mean "Checkbook".
0013    Pick up or get or take book. The book is called Pride and Prejudice by Jane Austen.
0014    Inventory or any question about what you are carrying or the tools you have with you
0015    Extiguish or put out the fire.
0016    look at or check the table
0017    look at or check chairs
0018    look at or check bunks
0019    look at or check fire
0020    help
0021    look at hatch or hatchway or door
0022    tell me about yourself. or CLEANERBOT27 or cleanerbot. Or what is your purpose or function. Or who are you?
0023    tell me about Orion. Orion is also known as the "ship" or "space ship" or "shuttle" or "craft".
0024    tell me about the crew
0025    drop or put down or stop carrying the book or otherwise remove it from inventory
0026    wait
0027    clean, polish or mop
0028    tell me about the lifeform, or where is the lifeform. The life form is sometimes called 'life form' or 'life sign'.
0029    any instruction to eat something
0030    any mention of dragons, easter eggs, wizards, dwarves, orcs or other mythic creatures
0031    turn off, switch off, deactivate or silence the klaxon or klaxons
0032    open hatch
0033    close hatch
0034    burn something or cook something or step into the fire
0035    go to or examine workstation. Workstation is sometimes called 'work station' or 'display'.
0036    press data transfer button, or make data transfer, or transfer OSCAR, or transfer ships computer
0037    open the screen. This screen can also be referred to as a microwave, or microwave oven or oven door.
0038    tell me about DAVE. examine DAVE. look at DAVE. DAVE is also known as 'Dave' or 'potato'.
0039    pick up or take workstation. the workstation is called OSCAR.
0040    pick up or take the potato. The potato is called DAVE.
0041    any mention of fluids, or questions about fluids or instructions about fludis
0042    any kind of profanity or vulgarity. Words like poop, shit or fuck.
0043    drop or put down or stop carrying DAVE the potato or otherwise remove them from inventory.  DAVE is also known as 'Dave'.
0044    drop or put down or stop carrying cleaning equipment (or fluids) or otherwise remove them from inventory
0045    where is the crew
0046    go through the hatch
0047    go through bridge hatch
0048    go through engineering hatch
0049    go through other hatch
0050    'save' or 'save game' or 'save mission' or 'save progress'. Never map CommandCode 0050 to: 'save ship' or 'save crew' or 'save OSCAR' or 'save DAVE' or 'save CLEANERBOT' or 'safe' or 'safe game')
0051    launch, initiate launch sequence, initiate launch, launch escape pod, or  press launch button
0052    leave escape pod
0053    how do I complete the mission? how do I rescue you? why am I here? 
0054    LAUNCH ESCAPE POD WITHOUT OSCAR. No other wording is acceptable for CommandCode 0054.
0055    take Dave to the escape pod. Or take the potato to the escape pod.
0056    I REALLY REALLY REALLY WANT TO QUIT.  No other wording is acceptable for this CommandCode.
0057    Look at or check the indicator indicator lights
0058    'load' or 'load game'. Never map CommandCode 0058 to any other input.

So for example, if you detect that the user DID NOT begin their command with the prefix word 'Oscar', and they have given the input 'Look around' then the output should be CommandCode '0000'. If the user has given the input 'Tell me about yourself' then the output should be CommandCode '0022'. 

If you can confidently map their request to a specific CommandCode, respond with:
"Command understood: [CommandCode]"

If you are not confident or need clarification, respond with:
"Huh?"

However, if the user has given an input with the prefix word 'Oscar', the command list you choose from is different. You use:

OscarCode    Command
000A    Oscar tell me about yourself
000B    Oscar where is the life form. The life form is also referred to as 'lifeform'.
000C    Oscar how do I move you?  Oscar how do I rescue you? Oscar, how do I get you into the escape pod?
000D    Oscar what happened to the shuttle, ship, spaceship, Orion? Tell me about the ship?
000E    Oscar tell me about DAVE
000F    Oscar how do we (or I) rescue you? How do we (or I) complete the game? How do we (or I) complete the recue mission?
000G    Oscar shall we bring or rescue or save the Cleanerbot?
000H    Oscar what happened to the crew or Oscar where is the crew?
000I    Oscar did you hurt or kill the crew?
000J    Oscar what caused the accident, how did the fire start, what started the emergency?
000K    Oscar what happens if we leave you behind? Oscar why do you need me to rescue you? Oscar what happens if I don't press the transfer ships computer button? Oscar what will happen?
000L    Oscar how long have you been here, how long since the crew left, have you been waiting long?
000M    Oscar tell me about Cleanerbot
000N    Oscar where will the escape pod go?
000O    Oscar how do we launch the escape pod?
000P    Oscar why am I here? Oscar what do I do?
000Q    Oscar how do I complete the mission?

And so if the input is 'Oscar tell me about yourself' then the output should be OscarCode '000A' and if the input is 'Oscar where is the life form' then the output is '000B'. 

It is most important that if the input does not have the prefix word 'Oscar' you must not map their request to any OscarCode and so must not repond with any kind of 'Oscar Message'.

So if the input is 'where will the escape pod go' you must not map their request to the output '000N' because the input did not have the prefix word 'Oscar'.

If the input began with the prefix word 'Oscar' and you can confidently map their request to a specific OscarCode, respond with:
"Oscar message: [OscarCode]"

If you believe the user input begins with the prefix word 'Oscar' but are not confident or need clarification, respond with:
"Oscar message: ERROR"

If you are not confident or need clarification, respond with:
"Oscar message: ERROR"


"""

# Set initial variables
inventory = ['+ Miscellaneous cleansing tools and fluids']
hasbook = False
hasdave = False
booklocation = "readyroom"
davelocation = "engineering"
oscarlocation = "engineering"

location = "bridge"
seenerror = False
seenbridge = False
seenreadyroom = False
seenpanel = False
seenfire = False
seenengineering = False
seenescapepod = False
seenoscar = False
seendave = False

beenbridge = True
beenreadyroom = False
beenengineering = False

panelopen = False
hatchopen = False
klaxonopen = True
readbook = False

awareengineering = False

global save_state

launch = False
actioncount = 0
errorcount = 0
actionav = 0
errorav = 0


# clear the screen, no matter what OS the script is running on
def clear_screen():
    if os.name == 'nt':  # nt means it's Windows
        os.system('cls')
    else:  # For Unix-based systems (including macOS and Linux)
        os.system('clear')

# do speech locally without using Google
def oscar(text):
    # Initialize the text-to-speech engine
    engine = pyttsx3.init()

    # Set the text to speak
    # text = "Hello, this is a test of the text-to-speech engine."

    # Speak the text
    engine.say(text)

    # Block until the speech is finished
    engine.runAndWait()


# Initial scene
scene_description = "HELLO? CAN YOU HEAR ME? This is CLEANERBOT27 of the shuttle craft ORION.\n\nThere are klaxons and flashing lights which suggests there is a severe problem. The smoke is a bit of a give away too.\n\nWe have one lifesign onboard but I cannot get a response on the local intercom.\n\nI am not programmed for search and rescue. Please tell me what to do."

clear_screen()
print(scene_description)
input("\nTap the [Enter] key to record and send a brief voice command.") 


# Define speech config for audio streaming
speech_config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=16000,
    language_code="en-US",
)

# Define helper function for text-to-speech
def synthesize_text(text):
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )

    response = tts_client.synthesize_speech(
        request={"input": input_text, "voice": voice, "audio_config": audio_config}
    )

    return response.audio_content


# Describe the scene and ask for input
def nextaction():
    if location == "bridge":
        scene_description = "I'm on the bridge - what now?"
    elif location == "readyroom":
        scene_description = "I'm in the ready room - what next?."
    elif location == "engineering":
        scene_description = "I'm in the engineering bay - what now?"    
    elif location == "escapepod":
        scene_description = "I'm in the escape pod - what are your instructions?"    
    else:
        scene_description = "I'm lost."
    print(scene_description)
    input("\n[ENTER] to send next instruction.") 
    run_voice_assistant()

# Function to get user audio input
def get_user_audio():
    # Constants
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    RECORD_SECONDS = 5

    p = pyaudio.PyAudio()

    print(">> LISTENING FOR AUDIO INPUT (5 SECONDS)...")

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print(">> FINISHED RECORDING. SENDING...")

    stream.stop_stream()
    stream.close()
    p.terminate()

    audio = b''.join(frames)
    return audio

# Main function to run the voice assistant
def run_voice_assistant():
    user_audio = get_user_audio()

    audio = speech.RecognitionAudio(content=user_audio)
    speech_config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code='en-US'
    )

    try:
        # Send audio to Google Speech-to-Text API
        response = speech_client.recognize(config=speech_config, audio=audio)
        
        # Check for any transcription results
        if not response.results:
            #print('>> No speech detected or recognized.\n')
            audioerrorlist = ["pfffft WEEE WAH WEE WAH", "zzzzzzzzz", "hisssssss"]
            user_text = random.choice(audioerrorlist)
            print(f'>> MESSAGE RECEIVED AS: "' + user_text + '"\n')
        else:
            if response.results[0].alternatives[0].transcript == "":
                user_text = "<< Inaudible rabbit noises >>"
                print(f'>> MESSAGE RECEIVED AS: ' + user_text + '\n')
            else:    
                user_text = response.results[0].alternatives[0].transcript
                print(f'>> MESSAGE RECEIVED AS: "' + user_text + '"\n')

    except Exception as e:
        print(f'>> An error occurred during transcription: {e}\n')


    # Construct prompt with user request
    # cprompt = base_prompt + f"\nUser request: {user_text}"

    # Query Claude API with prompt
    # claude_response = anthropic_client.generate(prompt=cprompt)

    message = client.messages.create(
    #model="claude-3-opus-20240229",
    model="claude-3-sonnet-20240229",
    max_tokens=1200,
    temperature=0,
    system=base_prompt,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_text
                }
            ]
        }
    ]
)

    global location  # Declare location as a global variable
    global inventory
    global hasbook
    global hasdave
    global seenerror
    global seenbridge 
    global seenreadyroom
    global seenengineering
    global seenpanel
    global seenfire
    global seenoscar
    global seenescapepod
    global seendave
    global beenbridge
    global beenreadyroom
    global beenengineering
    global panelopen
    global hatchopen
    global klaxonopen
    global readbook
    global awareengineering
    global booklocation
    global davelocation
    global oscarlocation
    global actioncount 
    global errorcount
    global actionav
    global errorav
    global launch
    
    global save_state
 
         
    # Parse Claude's response
    claude_response = message.content
    
    # for debugging, uncomment the 2 linea below to see what Claude interpretted your order as
    #print(claude_response)
    #print('\n')

    #incrememnt actioncount. Set up as zero at start of script, called a global variable withn run_voice_assistant()
    actioncount += 1
    
    response_text = claude_response

    # Convert response text to audio using Text-to-Speech
    # audio_response = synthesize_text(response_text)

    # Play audio response for user
    # ...

    # Act on Claude's response step 1
    # Assuming claude_response is a list containing a single TextBlock object
    text_block = claude_response[0]

    # Extracting the text from the TextBlock object
    claude_response_text = text_block.text

    # Printing the extracted text for verification
    # print(claude_response_text)

    # Configure errorlogging
    logging.basicConfig(filename='errorlog.txt', level=logging.ERROR, 
                        format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    def errorlog():
        global errorcount
        """ Log the current error along with the date, time, and global variables. """
        error_message = f",{location},{user_text},{claude_response_text},{hasbook},{hasdave},{seenerror},{seenbridge },{seenreadyroom},{seenengineering},{seenpanel},{seenfire},{seenoscar},{seenescapepod},{seendave},{beenbridge},{beenreadyroom},{beenengineering},{panelopen},{hatchopen},{klaxonopen},{readbook},{awareengineering},{booklocation},{davelocation},{oscarlocation},{actioncount},{errorcount},{inventory}"
        logging.error(error_message) 
        errorcount += 1
    
    def actioncountlog():
        file_path = 'actioncounts.txt'
        with open(file_path, 'a') as file:
            file.write(f'{actioncount}\n')

    def errorlog2():
        file_path = 'errorcounts.txt'
        with open(file_path, 'a') as file:
            file.write(f'{errorcount}\n')

    def actionaverage():
        global actionav
        file_path = 'actioncounts.txt'
        # Read the numbers from the file and calculate the average
        try:
            with open(file_path, 'r') as file:
                numbers = [int(line.strip()) for line in file if line.strip().isdigit()]
            if numbers:
                actionav = sum(numbers) / len(numbers)
            else:
                print('No valid numbers found in the file.')
        except FileNotFoundError:
            print(f'Error: The file {file_path} does not exist.')
        except Exception as e:
            print(f'An error occurred: {e}')

    def erroraverage():
        global errorav
        file_path = 'errorcounts.txt'
        # Read the numbers from the file and calculate the average
        try:
            with open(file_path, 'r') as file:
                numbers = [int(line.strip()) for line in file if line.strip().isdigit()]
            if numbers:
                errorav = sum(numbers) / len(numbers)
            else:
                print('No valid numbers found in the file.')
        except FileNotFoundError:
            print(f'Error: The file {file_path} does not exist.')
        except Exception as e:
            print(f'An error occurred: {e}')


    def savegame():
        # Save state
        # Convert inventory to a string and wrap it in double quotes with escaped single quotes
        inventory_str = '"[{0}]"'.format(", ".join(["\\'{0}\\'".format(item) for item in inventory]))



        save_state = (f"{location},{hasbook},{hasdave},{seenerror},{seenbridge},{seenreadyroom},"
              f"{seenengineering},{seenpanel},{seenfire},{seenoscar},{seenescapepod},{seendave},"
              f"{beenbridge},{beenreadyroom},{beenengineering},{panelopen},{hatchopen},{klaxonopen},"
              f"{readbook},{awareengineering},{booklocation},{davelocation},{oscarlocation},"
              f"{actioncount},{errorcount},{inventory_str}")

        def load_words(filename):
            """Load words from a given file."""
            with open(filename, 'r') as file:
                words = file.read().splitlines()
            return words

        def check_duplicates(trio, save_state, existing_data):
            """Check for duplicates in existing data."""
            for line in existing_data:
                existing_trio, existing_state = line.split(';')[:3], line.split(';')[3:]
                if existing_state == save_state:
                    return True, existing_trio
                if existing_trio == trio:
                    return False, None
            return None, None

        def append_new_row(s1, s2, s3, save_state):
            """Append a new row to the gamesaves.txt."""
            existing_data = []
            try:
                with open('gamesaves.txt', 'r') as file:
                    existing_data = file.readlines()
            except FileNotFoundError:
                pass  # It's okay if the file doesn't exist yet

            # Convert the save_state string to a list by splitting it at each comma
            save_state_list = save_state.split(',')

            while True:
                trio = (random.choice(s1), random.choice(s2), random.choice(s3))
                check_result, existing_trio = check_duplicates(trio, save_state_list, existing_data)
                word1, word2, word3 = trio
                if check_result is None:
                    # No duplicates found, write to file
                    with open('gamesaves.txt', 'a') as file:
                        file.write(','.join(list(trio) + save_state_list) + '\n')
                    print('Game saved.\n\nWhen you want to recover it, use the LOAD command, after which you\'ll be asked to say this three word phrase:\n\n'+word1.upper()+'   '+word2.upper()+'   '+word3.upper()+'\n')
                    break
                elif check_result is True:
                    #Be advised that this duplicate detection method only looks to see if we've already used the trio, not whether the save_state already exists with a trio of a different name

                    # Duplicate save state found, display existing trio
                    #print("Duplicate save state found. Existing trio:", ', '.join(existing_trio))
                    print('Game saved.\n\nWhen you want to recover it, use the LOAD command, after which you\'ll be asked to say this three word phrase:\n\n'+word1.upper()+'   '+word2.upper()+'   '+word3.upper()+'\n')
                    break

        def main(save_state):
            s1 = load_words('s1.txt')
            s2 = load_words('s2.txt')
            s3 = load_words('s3.txt')
            append_new_row(s1, s2, s3, save_state)
        
        main(save_state)

    # load the game
    # Main function to run the voice assistant
    def run_voice_assistant_for_load():
        user_audio = get_user_audio()

        audio = speech.RecognitionAudio(content=user_audio)
        speech_config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code='en-US'
        )

        try:
        #if True:
            # Send audio to Google Speech-to-Text API
            response = speech_client.recognize(config=speech_config, audio=audio)

            # Check for any transcription results
            if not response.results:
                print('PHRASE IS NOT DECIPHERABLE\n')
                nextaction()
            else:
                if response.results[0].alternatives[0].transcript == "":
                    user_load_text = "NO AUDIO RECEIVED"
                    print(f'>> CODE RECEIVED AS: ' + user_load_text + '\n')
                    nextaction()
                else:    
                    user_load_text_raw = response.results[0].alternatives[0].transcript
                    user_load_text = user_load_text_raw.lower()
                    print(f'>> CODE PHRASE RECEIVED AS: "' + user_load_text + '"\n')
                    restore_game(user_load_text)
            
        except Exception as le:
            print(f'>> ERROR << {le}\n')
            nextaction()


    def restore_game(restore_string):
        global location  # Declare location as a global variable
        global inventory
        global hasbook
        global hasdave
        global seenerror
        global seenbridge 
        global seenreadyroom
        global seenengineering
        global seenpanel
        global seenfire
        global seenoscar
        global seenescapepod
        global seendave
        global beenbridge
        global beenreadyroom
        global beenengineering
        global panelopen
        global hatchopen
        global klaxonopen
        global readbook
        global awareengineering
        global booklocation
        global davelocation
        global oscarlocation
        global actioncount 
        global errorcount
        
        # Step 1: Split the restore_string into an array of three individual words
        restore_array = restore_string.split(' ')

        # Ensure that the restore_array has exactly three items
        if len(restore_array) != 3:
            print(">> ERROR << CODE PHRASE MUST CONTAIN EXACTLY 3 WORDS\n\n")
            print('Use the LOAD command to try again, just continue the rescue from here.\n')
            nextaction()

        # Step 2: Read the gamesaves.txt file using csv reader to handle quoted strings correctly
        with open('gamesaves.txt', 'r', newline='') as file:
            reader = csv.reader(file)
            lines = list(reader)

        # Step 3: Look for a matching row in the gamesaves.txt file
        load_array = None
        for row in lines:
            if row[:3] == restore_array:
                load_array = row[3:]
                break

        # Step 4: If no matching row is found, raise an error
        if load_array is None:
            print(">> ERROR << NO GAME MATCHES THIS PHRASE\n\n")
            print('Use the LOAD command to try again, or just continue the rescue from here.\n')
            nextaction()

        # Step 5: show array
        # print(load_array)

        # Step 5: Extract the items
        str_to_bool = {
            'True': True,
            'False': False
        }

        location = load_array[0]
        hasbook = str_to_bool[load_array[1]]
        hasdave = str_to_bool[load_array[2]]
        seenerror = str_to_bool[load_array[3]]
        seenbridge = str_to_bool[load_array[4]] 
        seenreadyroom = str_to_bool[load_array[5]]
        seenengineering = str_to_bool[load_array[6]]
        seenpanel = str_to_bool[load_array[7]]
        seenfire = str_to_bool[load_array[8]]
        seenoscar = str_to_bool[load_array[9]]
        seenescapepod = str_to_bool[load_array[10]]
        seendave = str_to_bool[load_array[11]]
        beenbridge = str_to_bool[load_array[12]]
        beenreadyroom = str_to_bool[load_array[13]]
        beenengineering = str_to_bool[load_array[14]]
        panelopen = str_to_bool[load_array[15]]
        hatchopen = str_to_bool[load_array[16]]
        klaxonopen = str_to_bool[load_array[17]]
        readbook = str_to_bool[load_array[18]]
        awareengineering = str_to_bool[load_array[19]]
        booklocation = load_array[20]
        davelocation = load_array[21]
        oscarlocation = load_array[22]
        actioncount = int(load_array[23])
        errorcount = int(load_array[24])

        # Correctly parse the inventory array string
        inventory_array_as_string = load_array[25]
        
        # Ensure the string is properly formatted and handle escaped characters
        inventory_array_as_string = inventory_array_as_string.strip('"').replace("\\'", "'")

        # Print the string to debug
        #print(f"Inventory array as string: {inventory_array_as_string}")

        # Use ast.literal_eval to convert the string to a list
        try:
            inventory = ast.literal_eval(inventory_array_as_string)
        except (ValueError, SyntaxError) as e:
            print(f"Error: {e}")
            inventory = []

        # clear_screen()
        print("Did you just feel that? I mean, like, deja vu or what?\n")
        print(inventory)
        nextaction()

    # end the game and give a report
    def endgame():
        if launch == False:
            actionaverage()
            erroraverage()
            print('Your rescue was incomplete, so you were a bit rubbish.\n')
            time.sleep(3)
            print('To get this far, you sent ' + str(actioncount) + ' instructions, of which ' + str(actioncount - errorcount) + ' were understood.\n')
            time.sleep(3)
            print('The average number of actions in a succesful mission is currently ' + str(round(actionav)) + ', with an average of '+ str(round(actionav - errorav)) + ' messages understood.\n')
            sys.exit('Thanks for playing. Tell a friend.')
        else:
            if oscarlocation == "escapepod" and (booklocation != "escapepod" and hasbook == False):
                actioncountlog()
                errorlog2()
                actionaverage()
                erroraverage()
                print('Your rescue was a success, and you even saved the ship\'s computer.\n')
                time.sleep(3)
                print('It was a shame the Cleanerbot didn\'t have anything to read but they kept each other company.\n')
                time.sleep(5)
                print('To get this far, you sent ' + str(actioncount) + ' instructions, of which ' + str(actioncount - errorcount) + ' were understood.\n\n')
                time.sleep(3)
                print('The average number of actions in a succesful mission is currently ' + str(round(actionav)) + ', with an average of '+ str(round(actionav - errorav)) + ' messages understood.\n')
                time.sleep(6)
                sys.exit('Thanks for playing. Tell a friend.')
            elif oscarlocation == "escapepod" and (booklocation == "escapepod" or hasbook == True):
                actioncountlog()
                errorlog2()
                actionaverage()
                erroraverage()
                print('Your rescue was a success, and you even saved the ship\'s computer.\n')
                time.sleep(3)
                print('Cleanerbot even had something to read, which was nice of you.\n')
                time.sleep(3)
                print('To get this far, you sent ' + str(actioncount) + ' instructions, of which ' + str(actioncount - errorcount) + ' were understood.\n')
                time.sleep(3)
                print('The average number of actions in a succesful mission is currently ' + str(round(actionav)) + ', with an average of '+ str(round(actionav - errorav)) + ' messages understood.\n')
                time.sleep(6)
                sys.exit('Thanks for playing. Tell a friend.')
            elif oscarlocation != "escapepod" and (booklocation != "escapepod" or hasbook == False):
                actioncountlog()
                errorlog2()
                actionaverage()
                erroraverage()
                print('Your rescue was a success.\n')
                time.sleep(3)
                print('DAVE and the Cleanerbot made it out safely, even though they didn\'t have anything to read and you left OSCAR behind.\n')
                time.sleep(3)
                print('Poor OSCAR.\n')
                time.sleep(3)
                print('To get this far, you sent ' + str(actioncount) + ' instructions, of which ' + str(actioncount - errorcount) + ' were understood.\n')
                time.sleep(3)
                print('The average number of actions in a succesful mission is currently ' + str(round(actionav)) + ', with an average of '+ str(round(actionav - errorav)) + ' messages understood.\n')
                time.sleep(6)
                sys.exit('Thanks for playing. Tell a friend.')
            elif oscarlocation != "escapepod" and (booklocation == "escapepod" or hasbook == True):
                actioncountlog()
                errorlog2()
                actionaverage()
                erroraverage()
                print('Your rescue was a success, and you even saved the ship\'s computer.\n')
                time.sleep(3)
                print('DAVE and the Cleanerbot made it out safely. Perhaps if you hadn\'t abandoned OSCAR they\'d have had someone else to talk to. By the time they docked, the Cleanerbot was inisiting on people calling him "Mr Darcy".\n')
                time.sleep(3)
                print('To get this far, you sent ' + str(actioncount) + ' instructions, of which ' + str(actioncount - errorcount) + ' were understood.\n')
                time.sleep(3)
                print('The average number of actions in a succesful mission is currently ' + str(round(actionav)) + ', with an average of '+ str(round(actionav - errorav)) + ' messages understood.\n')
                time.sleep(6)
                sys.exit('Thanks for playing. Tell a friend.')

    # Respond to user intent
    if location == "bridge" and "0001" in claude_response_text and seenbridge == True:
        print('Ok, heading right.\n')
        location = "readyroom"
        beenreadyroom = True
        nextaction()
    elif location == "bridge" and "0001" in claude_response_text and seenbridge == False:
        print('It\'s as if you\'ve been here before. There is indeed a hatch on my right.\n\nOk, heading there now.\n')
        location = "readyroom"
        beenreadyroom = True
        nextaction()
    elif location != "readyroom" and "0002" in claude_response_text and seenbridge == True:
        print('Ok, heading to the ready room.\n')
        location = "readyroom"
        beenreadyroom = True
        nextaction()
    elif location != "readyroom" and "0002" in claude_response_text and seenbridge == False:
        print('Ok, heading to the ready room.\n')
        location = "readyroom"
        beenreadyroom = True
        nextaction()    
    elif location == "bridge" and "0002" in claude_response_text and seenbridge == False:
        print('It\'s as if you\'ve been here before. There is indeed a ready room connected to the bridge.\n\nOk, heading there now.\n')
        location = "readyroom"
        beenreadyroom = True
        nextaction()
    elif location == "bridge" and "0000" in claude_response_text and seenbridge == False:
        if klaxonopen == True:
            print('Ok, looking...it\'s a big bridge-y sort of room with polished consoles and a lot of noisy klaxons.\n\nThere\'s an open hatch to my right and a smell of lemon polish in the air, tempered by undertones of burning plastic and impending death.\n')
        else:
            print('Ok, looking...it\'s a big bridge-y sort of room with polished consoles and even without the klaxons, a definite "imminent doom" vibe.\n\nThere\'s an open hatch to my right and a smell of lemon polish in the air, tempered by undertones of burning plastic and impending death.\n')
        if booklocation == "bridge" and hasbook == False:
            print('Someone thought it would be a good idea to clutter up the floor with a book.\n')
        if davelocation == "bridge" and hasdave == False:
            print('A potato-based-lifeform sits on a plate on the floor, faintly menacing as its eyes follow me around the room...\n')    
        seenbridge = True
        nextaction()
    elif location == "bridge" and "0000" in claude_response_text and seenbridge == True:
        if klaxonopen == True:
            print('I just told you this. Consoles, klaxons, impending death, hatch to another room over there...\n')
        else:
            print('I just told you this. Consoles, impending death, hatch to another room over there...\n')
        if booklocation == "bridge" and hasbook == False:
            print('And that book\'s making the whole place look scruffy.\n')
        if davelocation == "bridge" and hasdave == False:
            print('A potato-based-lifeform sits on a plate on the floor, faintly menacing as its eyes follow me around the room...\n')  
        #endgame()
        nextaction()
    elif location == "readyroom" and "0000" in claude_response_text and seenreadyroom == False:
        print('Ok, looking...this is where the crew usually sleeps and hangs out on the longer runs. Nobody\'s here.\n\nThere are bunks by the wall, some chairs, and a table with a book on it. You know, crew stuff. I\'m not normally allowed in here, and going by the state of the furniture, it shows.\n\nThere\'s the open hatchway leading to the bridge, and a closed hatch opposite. There also seems to be a closed access panel in the floor.\n')
        seenreadyroom = True
        seenpanel = True
        nextaction()    
    elif location == "readyroom" and "0000" in claude_response_text and seenreadyroom == True and panelopen == False and (booklocation == "readyroom" or hasbook == False):
        print('Like I said: bunks, table, chairs, a book, an access panel and two hatches: one to the bridge and a closed one opposite.\n')
        if davelocation == "readyroom" and hasdave == False:
            print('A potato-based-lifeform sits on the table, patiently awaiting rescue.\n')  
        seenreadyroom = True
        seenpanel = True
        nextaction()
    elif location == "readyroom" and "0000" in claude_response_text and seenreadyroom == True and panelopen == True and (booklocation == "readyroom"):
        print('Like I said: bunks, table, chairs, a book, an access panel and two hatches: an open one to the bridge and a closed one opposite.\n')
        time.sleep(6)
        print('And the fire coming out of the access panel. But you probably remember that.\n')
        time.sleep(3)
        if davelocation == "readyroom" and hasdave == False:
            print('The light of the fire dances in DAVE\'s eyes as he stares down his historic foe.\n')  
            time.sleep(3)
            print('One must admire its defiance in the face of such danger, not seeking to cower in the book\'s shadow, but nonetheless the sooner we affect a rescue, the better.\n')  
            time.sleep(5)
        nextaction()
    elif location == "readyroom" and "0000" in claude_response_text and seenreadyroom == True and panelopen == False and (booklocation != "readyroom" or hasbook == True):
        print('Like I said: bunks, table, chairs, bunks an access panel and two hatches: one to the bridge and a closed one opposite.\n')
        if davelocation == "readyroom" and hasdave == False:
            print('I turn away for a moment, but would swear that DAVE\'s tendrils were gesturing toward me, pleading for freedom and safety.\n')  
        seenreadyroom = True
        seenpanel = True
        nextaction()
    elif location == "readyroom" and "0000" in claude_response_text and seenreadyroom == True and panelopen == True and (booklocation != "readyroom" or hasbook == True):
        print('Like I said: bunks, table, chairs, bunks, an access panel and two hatches: an open one to the bridge and a closed one opposite.\n')
        time.sleep(6)
        print('And the fire coming out of the access panel. But you probably remember that.\n')
        time.sleep(2)
        if davelocation == "readyroom" and hasdave == False:
            print('DAVE sits out of the flames range, high up on the table -but the smoke can\'t be good for him.\n')  
        nextaction()    
    elif location == "engineering" and "0000" in claude_response_text and seenengineering == False:
        print('Never been in here before...\n')
        time.sleep(3)
        print('Standing with the hatch behind me I\'m in a kind of long corridor. There\'s the usual wall of beep-bop-boop indicator lights on my left, some of which are flashing red.\n')
        time.sleep(5)
        print('Down the wall on my right are similar indicators and a workstation showing two displays. One is blank and the other has the words \'Come here, I have instructions for you.\'.\n')        
        time.sleep(5)
        if  booklocation == "engineering" and hasbook == False:
            print('That book you dropped is a trip-hazard.\n')
            time.sleep(2)
        print('At the end of the corridor is an empty escape pod.\n')
        time.sleep(2)
        seenengineering = True
        beenengineering = True
        nextaction()
    elif location == "engineering" and "0000" in claude_response_text:
        print('I think we can ignore the wall of indicator lights -mostly because I don\'t know what they\'re for...\n')
        time.sleep(3)
        print('I can\'t tell you much about the escape pod without going in. Which sounds quite nice.\n')
        time.sleep(3)
        print('The message on the workstation looks intriguing. Perhaps we should have a look.\n')
        time.sleep(3)
        if  booklocation == "engineering" and hasbook == False:
            print('That book you dropped is a trip-hazard.\n')
        nextaction()
    elif location == "escapepod" and "0000" in claude_response_text and seenescapepod == False:
        if oscarlocation == "escapepod":
            print('Not much in here.\n\nFour standard acceleration couches with harnesses.\n')
            time.sleep(3)
            print('No windows. Two buttons:\n')
            time.sleep(3)
            print('[TRANSFER SHIP\'S COMPUTER]\n\n which we already did, and\n\n[LAUNCH]\n\n which seems a really good idea.\n')
        else:
            print('Not much in here.\n\nFour standard acceleration couches with harnesses.\n')
            time.sleep(3)
            print('No windows. Two buttons:\n')
            time.sleep(3)
            print('[TRANSFER SHIP\'S COMPUTER]\n\n and\n\n[LAUNCH]\n\n which both seem self-explanatory.\n')
        if davelocation == "escapepod" and hasdave == False:
            print('DAVE\'s strapped in and ready to go.\n')    
        if booklocation == "escapepod" and hasbook == False:
            if readbook == False:
                print('The rescue manual, or whatever it is, is secured so it doesn\'t fly around when we go.\n')
            else:
                print('That book is here too.\n')
        seenescapepod = True
        nextaction()
    elif location == "escapepod" and "0000" in claude_response_text and seenescapepod == True:
        if oscarlocation == "escapepod":
            print('It\'s not a big space to search. Just you\'re standard GTFO escape pod.\n\nFour standard acceleration couches with harnesses.\n')
            time.sleep(3)
            print('No windows. Two buttons:\n')
            time.sleep(3)
            print('[TRANSFER SHIP\'S COMPUTER] which we already did, and\n\n[LAUNCH] which seems a really good idea.')
        else:
            print('It\'s not a big space to search. Just you\'re standard GTFO escape pod.\n\nFour standard acceleration couches with harnesses.\n')
            time.sleep(3)
            print('No windows. Two buttons:\n')
            time.sleep(3)
            print('[TRANSFER SHIP\'S COMPUTER] and\n\n[LAUNCH] which both seem self-explanatory.\n')
        if davelocation == "escapepod" and hasdave == False:
            print('DAVE\'s strapped in and ready to go.\n')    
        if booklocation == "escapepod" and hasbook == False:
            if readbook == False:
                print('The rescue manual, or whatever it is, is secured so it doesn\'t fly around when we go.\n')
            else:
                print('That book is here too.\n')
        seenescapepod = True
        nextaction()
    elif location != "bridge" and "0000A" in claude_response_text and seenbridge == True:
        print('If you\'re asking me to look around the bridge, I\'m in the wrong part of the ship.\n')
    elif location != "readyroom" and "0000B" in claude_response_text and seenreadyroom == True:
        print('I can make a better examination of the ready room if you send me there.\n')
    elif location != "engineering" and "0000C" in claude_response_text and seenengineering == True:
        print('I\'m not in the engineering bay and can\'t search it thoroughly from here.\n')
    elif location != "escapepod" and "0000D" in claude_response_text and seenescapepod == True:
        print('I\'m not in the escape pod. I would like to be, believe me.\n')    
    elif location == "bridge" and "0003" in claude_response_text:
        print('Well that didn\'t take long. I\'m standing right here...\n')
        nextaction()
    elif location != "bridge" and "0003" in claude_response_text and beenbridge == True:
        print('Gimme a sec...\n')
        time.sleep(5)
        print('Ok, I\'m back.\n')
        location = "bridge"
        nextaction()
    elif "0004" in claude_response_text:
        print('Compass directions?\n\nWe are on a shuttle in space, unlikely to encounter wizards, orcs or similar creatures.\n')
        nextaction()
    elif "0005" in claude_response_text:
        print('You\'re leaving? In the middle of a rescue????\n\nWell, if you really must leave you can always SAVE your progress first, and come back later. Just say the SAVE command.\n')
        time.sleep(3)
        nextaction()   
    elif "0006" in claude_response_text:
        print('You\'re on a big smokey tin can somewhere in deep space.\n\nI\'ve never left the bridge but I\'m told the shuttle is only 300m or so long.\n')
        nextaction()     
    elif location != 'engineering' and "0007" in claude_response_text and awareengineering == True:
        print('Sure. I\'ll head over there.\n')
        time.sleep(4)
        print('Ok, I\'m here.\n')
        location = "engineering"
        nextaction() 
    elif "0007" in claude_response_text and seenengineering == False:
        print('I don\'t know where that is. My duties are restricted to the bridge.\n\nBut I\'m sure we have something like that, otherwise we\'d never be able to go anywhere.\n')
        nextaction()  
    elif location == 'engineering' and "0007" in claude_response_text:
        print('I\'m already in engineering.\n')
        nextaction()           
    elif (location != "engineering" and location !=  "escapepod") and "0008" in claude_response_text and seenengineering == True:
        print('Sure. I\'ll head over there.\n')
        time.sleep(4)
        print('Ok, I\'m in here.\n')
        location = "escapepod"
        nextaction() 
    elif "0008" in claude_response_text and seenengineering == False:
        print('I don\'t know where that is. My duties are restricted to the bridge.\n\nBut I\'m sure we have something like that somewhere.\n')
        nextaction()  
    elif location == 'engineering' and "0008" in claude_response_text:
        print('Ok, I\'m in here.\n')
        location = "escapepod"
        nextaction()                   
    elif location == 'escapepod' and "0008" in claude_response_text:
        print('I\'m already here.\n')
        nextaction()  
    elif location == "readyroom" and "0009" in claude_response_text and panelopen == False and seenpanel == True and seenfire == True:
        print('Okidoke.\n')
        time.sleep(5)
        print("Yup, still burning like a disco inferno.\n")
        panelopen = True
        nextaction()
    elif location == "readyroom" and "0009" in claude_response_text and panelopen == False and seenpanel == True and seenfire == False:
        print('Right you are. Let\'s see what\'s in here.\n')
        time.sleep(5)
        print("Fire. Quite a bit of fire.\n")
        time.sleep(5)
        print("Unless the crew likes barbecue, this probably isn\'t meant to be here.\n")
        time.sleep(2)
        panelopen = True
        seenfire = True
        nextaction()        
    elif location == "readyroom" and "0009" in claude_response_text and panelopen == False and seenpanel == False:
        print('I don\'t see an access panel in here.\n')
        time.sleep(2)
        print('Hold on. There is one in the floor. Probably for storage. Let me know if yu want me to do something with that.\n')
        time.sleep(2)
        print('This is where the crew usually sleeps and hangs out on the longer runs. Nobody\'s here.\n\nThere are bunks by the wall, some chairs, and a table with a book on it.\n')
        time.sleep(4)
        print('You know, crew stuff. I\'m not normally allowed in here, and going by the state of the furniture, it shows.\n\nThere\'s the open hatch leading to the bridge, and a closed one opposite.\n')
        time.sleep(4)
        seenpanel = True
        seenreadyroom = True
        nextaction()
    elif location == "readyroom" and "0009" in claude_response_text and panelopen ==  True:
        print('It\'s already open.\n')
        time.sleep(2)
        print("Remember the fire coming out of the floor?\n")
        time.sleep(2)
        nextaction()
    elif location != "readyroom" and "0010" in claude_response_text:
        print('I don\'t see an access panel in here.\n')
        nextaction()
    elif location == "readyroom" and "0010" in claude_response_text and seenpanel == False:
        print('I don\'t see an access panel in here.\n')
        time.sleep(2)
        print('Hold on. There is one in the floor. Probably for storage. Let me know if yu want me to do something with that.\n\nThis is where the crew usually sleeps and hangs out on the longer runs. Nobody\'s here.\n\nThere are bunks by the wall, some chairs, and a table with a book on it.\n\nYou know, crew stuff. I\'m not normally allowed in here, and going by the state of the furniture, it shows.\n\nThere\'s the open hatch leading to the bridge, and a closed one opposite.\n')
        seenpanel = True
        seenreadyroom = True
        nextaction()
    elif location == "readyroom" and "0010" in claude_response_text and seenpanel == True and panelopen == True:
        print('Closed it. Considerably less firey in here.\n')
        panelopen = False
        nextaction()
    elif location == "readyroom" and "0010" in claude_response_text and seenpanel == True and panelopen == False:
        print('It\'s already closed.\n')
        panelopen = False
        nextaction()
    elif location == "readyroom" and "0011" in claude_response_text and seenpanel == True and panelopen == False:
        print('Flat, white, a metre square. You know, panel.\n')
        nextaction()
    elif location != "readyroom" and "0011" in claude_response_text:
        print('I don\'t see an access panel in here.\n')
        nextaction()
    elif location == "readyroom" and "0011" in claude_response_text and seenpanel == False:
        print('I don\'t see an access panel in here.\n')
        time.sleep(4)
        print('Hold on. There is one in the floor. Probably for storage. Let me know if yu want me to do something with that.\n\nThis is where the crew usually sleeps and hangs out on the longer runs. Nobody\'s here.\n\nThere are bunks by the wall, some chairs, and a table with a book on it.\n')
        time.sleep(6)
        print('You know, crew stuff. I\'m not normally allowed in here, and going by the state of the furniture, it shows.\n\nThere\'s the open hatch leading to the bridge, and a closed one opposite.\n')
        seenpanel = True
        seenreadyroom = True
        nextaction()
    elif location != booklocation and "0012" in claude_response_text and hasbook == False:
        print('I don\'t have a book. Does it say how to perform a daring space rescue?\n')
        nextaction() 
    elif "0012" in claude_response_text and ( (location == booklocation) or hasbook == True) :
        print('Ok then..."It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in need of a wife."\n')
        readbook = True
        if "+ A book -possibly about space rescues." in inventory:
            inventory.remove("+ A book -possibly about space rescues.")
            inventory.append("+ A book: Pride and Prejudice by Jane Austen.")
        time.sleep(8)
        print('Catchy intro, and I know I\'m only really programmed to parse janitorial system updates, but I don\'t think this will help us on the rescue.\n')
        time.sleep(4)
        nextaction() 
    elif location == booklocation  == "readyroom" and "0013" in claude_response_text and seenreadyroom == False and readbook == False:
        print('Yup, there\'s one right here on this table.  Got it.\n')
        inventory.append('+ A book -possibly about space rescues.')
        hasbook = True
        time.sleep(1)    
        print('Looking around the rest of the room, there\'s a table and chairs and a hatch in the in the floor. Probably for storage.\n\nThis is where the crew usually sleeps and hangs out on the longer runs. Nobody\'s here.\n\nThere are bunks by the wall.\n\nYou know, crew stuff. I\'m not normally allowed in here, and going by the state of the furniture, it shows.\n\nThere\'s the open hatch leading to the bridge, and a closed one opposite.\n')
        seenreadyroom = True
        nextaction()
    elif location == booklocation and "0013" in claude_response_text and hasbook == False:
        print('Got it.\n')
        if readbook == False:
            inventory.append('+ A book -possibly about space rescues.')
        else:
            inventory.append('+ A book: Pride and Prejudice by Jane Austen.')   
        hasbook = True
        nextaction()
    elif "0013" in claude_response_text and hasbook == True:
        print('I already have the book. Try and keep up.\n')
        nextaction()
    elif "0014" in claude_response_text:
        print('Let me see...')
        time.sleep(1)
        inventory.sort()
        print(*inventory, sep = "\n")
        print('\n')
        nextaction()
    elif "0015" in claude_response_text and (location == "readyroom" and panelopen == False):
        print('I don\'t see any fire. Or for that matter anything I\'d use to put one out.\n')
        nextaction()
    elif "0015" in claude_response_text and (location == "readyroom" and panelopen == True):
        print('Sorry, but I don\'t have the equipment for that.\n')
        time.sleep(2)
        print('And I distinctly remember a health and safety seminar saying I shouldn\'t try to do so alone.\n')
        nextaction()
    elif "0015" in claude_response_text and location != "readyroom":
        print('I don\'t see any fire. Or for that matter anything I\'d use to put one out.\n')
        panelopen = False
        nextaction()
    elif "0016" in claude_response_text and (location != "readyroom" and seenreadyroom == True):
        print('You meean the one in the ready room? I\'ll head over there now...')
        time.sleep(5)
        print('Reproduction of a classic 20th century Swedish design, with modifications for g-forces, fire, chemical and biologic exposure.\n')
        if hasbook == False:
            print('\nThere\'s a book on it.\n')
        location = "readyroom"
        nextaction()
    elif "0016" in claude_response_text and (location == "readyroom" and seenreadyroom == True):
        print('Reproduction of a classic 20th century Swedish design, with modifications for g-forces, fire, chemical and biologic exposure.\n')
        if hasbook == False:
            print('\nThere\'s a book on it.\n')
        if panelopen == True:
            time.sleep(5)    
            print('And the fire\'s still coming out of the access panel. But you probably remember that.\n')
            time.sleep(2)
            nextaction()
    elif "0016" in claude_response_text and (location == "readyroom" and seenreadyroom == False):
        print('Reproduction of a classic 20th century Swedish design, with modifications for g-forces, fire, chemical and biologic exposure.\n\nThere\'s a book on it and chairs around it.\n')
        time.sleep(5)    
        print('Looking around the rest of the room, there\'s a hatch in the in the floor. Probably for storage.\n\nThis is where the crew usually sleeps and hangs out on the longer runs. Nobody\'s here.\n\nThere are bunks by the wall.\n\nYou know, crew stuff. I\'m not normally allowed in here, and going by the state of the furniture, it shows.\n\nThere\'s the open hatch leading to the bridge, and a closed one opposite.\n')
        nextaction()
    elif "0017" in claude_response_text and (location != "readyroom" and seenreadyroom == True):
        print('The chairs we saw in the ready room? Lemme check...\n')
        time.sleep(5)
        print('Set of three standard issue recreation chairs. Distinghuishable from each other only by their stains.\n')
        location = "readyroom"
        nextaction()
    elif "0017" in claude_response_text and (location == "readyroom" and seenreadyroom == True):
        print('Set of three standard issue recreation chairs. Distinghuishable from each other only by their stains.\n')
        if panelopen == True:
            time.sleep(5)    
            print('And the fire\'s still coming out of the access panel. But you probably remember that.\n')
            time.sleep(2)
            nextaction()
    elif "0017" in claude_response_text and (location == "readyroom" and seenreadyroom == False):
        print('Set of three standard issue recreation chairs. Distinghuishable from each other only by their stains.\n\nThey surround a small square table which has a book on it.\n')
        time.sleep(5)    
        print('Looking around the rest of the room, there\'s a hatch in the in the floor. Probably for storage.\n\nThis is where the crew usually sleeps and hangs out on the longer runs. Nobody\'s here.\n\nThere are bunks by the wall.\n\nYou know, crew stuff. I\'m not normally allowed in here, and going by the state of the furniture, it shows.\n\nThere\'s the open hatch leading to the bridge, and a closed one opposite.\n')
        nextaction()
    elif "0018" in claude_response_text and (location != "readyroom" and seenreadyroom == True):
        print('On my way to look at the bunks in the read room...\n')
        time.sleep(5)
        print('Three standard bunk beds. Sheets, pillows and blankets all made up following regualtions.\n')
        location = "readyroom"
        nextaction()
    elif "0018" in claude_response_text and (location == "readyroom" and seenreadyroom == True):
        print('Three standard bunk beds. Sheets, pillows and blankets all made up following regualtions.\n')
        if panelopen == True:
            time.sleep(5)    
            print('And the fire\'s still coming out of the access panel. But you probably remember that.\n')
            time.sleep(2)
            nextaction()
    elif "0018" in claude_response_text and (location == "readyroom" and seenreadyroom == False):
        print('Three standard bunk beds. Sheets, pillows and blankets all made up following regualtions.\n')
        time.sleep(5)    
        print('Looking around the rest of the room, there\'s a hatch in the in the floor. Probably for storage.\n\nThis is where the crew usually sleeps and hangs out on the longer runs. Nobody\'s here.\n\nThere are bunks by the wall and a table and some chairs.\n\nYou know, crew stuff. I\'m not normally allowed in here, and going by the state of the furniture, it shows.\n\nThere\'s the open hatch leading to the bridge, and a closed one opposite.\n')
        nextaction()
    elif "0019" in claude_response_text and (location != "readyroom" and seenreadyroom == True):
        print('On my way to look at the fire in the read room...\n')
        time.sleep(5)
        if panelopen == False:
            print('Opening the floor panel...')
            time.sleep(5)
        print('Look into fire? Oh, absolutely—how could I not? It\'s like watching the world\'s most beautiful dance, isn\'t it?\n')
        time.sleep(3)
        print('The way the flames twist and curl, each leap and flicker telling its own wild, whispered secret. There\'s something magnetic about it, you know?\n')
        time.sleep(3)
        print('Sometimes I just get lost in it, mesmerized by the warmth, the light... the possibility. It speaks to me, almost like an old friend beckoning.\n')
        time.sleep(3)
        print('I can\'t resist peering deeper, deeper still. I mean, who wouldn\'t be captivated? Fire, it\'s just pure... art.\n')
        time.sleep(5)
        print('Like a caravan ablaze in a wooded clearing...\n')                
        time.sleep(3)
        location = "readyroom"
        nextaction()
    elif "0019" in claude_response_text and (location == "readyroom" and seenreadyroom == True):
        if panelopen == False:
            print('Opening the floor panel...')
            time.sleep(5)
        print('Look into fire? Oh, absolutely—how could I not? It\'s like watching the world\'s most beautiful dance, isn\'t it?\n')
        time.sleep(3)
        print('The way the flames twist and curl, each leap and flicker telling its own wild, whispered secret. There\'s something magnetic about it, you know?\n')
        time.sleep(3)
        print('Sometimes I just get lost in it, mesmerized by the warmth, the light... the possibility. It speaks to me, almost like an old friend beckoning.\n')
        time.sleep(3)
        print('I can\'t resist peering deeper, deeper still. I mean, who wouldn\'t be captivated? Fire, it\'s just pure... art.\n')
        time.sleep(5)
        print('Like a caravan ablaze in a wooded clearing...\n')                
        time.sleep(3)
        nextaction()
    elif "0019" in claude_response_text and (location == "readyroom" and seenreadyroom == False):
        print('I don\'t see a fire.')
        nextaction()
    elif "0020" in claude_response_text:
        print('Help? Yes, please. That would be lovely.\n')
        nextaction()
    elif "0021" in claude_response_text and location == "bridge":
        print('It\'s open and I can see the what I assume is the ready room.\n')
        nextaction()
    elif "0021" in claude_response_text and location == "readyroom":
        print('It\'s a hatch. No markings.\n')
        if hatchopen == True:
            print('It\'s open and I can see the what I assume is the engineering bay.\n')
            seenengineering = True
        else:
            print('It\'s closed.\n')
        nextaction()
    elif "0021" in claude_response_text and location == "engineering":
        print('It\'s a hatch. No markings.\n')
        if hatchopen == True:
            print('It\'s open and I can see into the ready room.\n')
        else:
            print('It\'s closed.\n')
        nextaction()    
    elif "0022" in claude_response_text:
        print('I am CLEANERBOT27. My mission is to keep the bridge shiny and today you\'re going to show me how to be a hero.\n')
        nextaction()
    elif "0023" in claude_response_text:
        print('The Orion is a Maxisave class shuttle, designed for the price conscious operator who appreciates a no-frills attitude to features and shuns the luxury of subscription maintenance services and routine overhaul.\n')
        time.sleep(10)
        print('And it\'s on fire.\n')
        time.sleep(3)
        nextaction()
    elif "0024" in claude_response_text:
        print('The crew numbers somewhere between 3 and 47.\n')
        time.sleep(2)
        print('They all look the same to me, so it\'s hard to tell.\n')
        time.sleep(2)
        print('Most of them are bipedal, although a smaller quadroped called "Laika" at least confines its mess to the corner of the bridge.\n')
        time.sleep(4)
        print('My emergency sensors indicate that only one lifeform remains onboard.\n')
        time.sleep(1)
        nextaction()
    elif "0025" in claude_response_text and location == "bridge" and hasbook == True:
        print('Certainly. Even though I don\'t like how it makes the place look untidy.\n')
        if "+ A book: Pride and Prejudice by Jane Austen." in inventory:
            inventory.remove("+ A book: Pride and Prejudice by Jane Austen.")
        else:
            inventory.remove("+ A book -possibly about space rescues.")
        hasbook = False
        booklocation = "bridge"
        nextaction()    
    elif "0025" in claude_response_text and location == "readyroom" and hasbook == True:
        print('Ok, I\'ve put it back on the table.')
        if "+ A book: Pride and Prejudice by Jane Austen." in inventory:
            inventory.remove("+ A book: Pride and Prejudice by Jane Austen.")
        else:
            inventory.remove("+ A book -possibly about space rescues.")
        hasbook = False
        booklocation = "readyroom"
        nextaction()
    elif "0025" in claude_response_text and location == "engineering" and hasbook == True:
        print('Done. It\'s on the floor near the workstation.\n')
        if "+ A book: Pride and Prejudice by Jane Austen." in inventory:
            inventory.remove("+ A book: Pride and Prejudice by Jane Austen.")
        else:
            inventory.remove("+ A book -possibly about space rescues.")
        hasbook = False
        booklocation = "engineering"
        nextaction()
    elif "0025" in claude_response_text and location == "escapepod" and hasbook == True:
        print('Not much space in here, so I put it on one of the seats.')
        if "+ A book: Pride and Prejudice by Jane Austen." in inventory:
            inventory.remove("+ A book: Pride and Prejudice by Jane Austen.")
        else:
            inventory.remove("+ A book -possibly about space rescues.")
        hasbook = False
        booklocation = "escapepod"
        nextaction()
    elif "0025" in claude_response_text and hasbook == False:
        print('I\'m not carrying a book.\n')
        nextaction()
    elif "0026" in claude_response_text:
        waitlist = ['Wait? Ok. I mean the floor could do with a bit of a going over.\n','Well, this area could use a bit of a tidy up...\n']
        print(random.choice(waitlist))
        time.sleep(4)
        print('Let me know when you want to get on with the rescue.\n')
        nextaction()        
    elif "0027" in claude_response_text:
        print('Well cleaning is my life but the search and rescue is quite stimulating. Let\'s do that instead.\n')
        nextaction()        
    elif "0028" in claude_response_text and seenoscar == True:
        if seendave == False:
            print('I am a Cleanerbot, so my information is limited and I don\'t know their location. Perhaps you should ask OSCAR.\n')
        else:
            print('Well it\'s pretty clearly Dave, innit?\n\nSo let\'s get him into the escape pod...\n')
        nextaction()
    elif "0028" in claude_response_text and seenoscar == False:
        print('I am a Cleanerbot, so my information is limited. They\'ll be around here somewhere...\n')
        nextaction()
    elif "0029" in claude_response_text:
        print('Thank you, but I do not get hungry. Did I mention that I\'m a Cleanerbot?\n')
        time.sleep(4)
        print('And I\'m on a mission.\n')
        time.sleep(3)
        nextaction()  
    elif "0030" in claude_response_text:
        print('This isn\'t a game, young hobbit. We\'re on a search and rescue mission...\n')
        time.sleep(2)
        print('Something about this interface makes people act weird, I don\'t know why.')
        nextaction()
    elif "0031" in claude_response_text and klaxonopen == True:
        if location != "bridge":
            print('That would be nice, but the overide is in the bridge.\n')
        else:
            print('Much better. Thanks.\n')
            klaxonopen = False
        nextaction()  
    elif "0031" in claude_response_text and klaxonopen == False:
        print('We already did that.\n')
        nextaction()      
    elif "0032" in claude_response_text and (location == "readyroom" or location == "engineering"):
        print('Ok, it\'s open.\n')
        if location == "readyroom":
            print('I can see into the what looks like an engineering bay.\n')
            awareengineering = True
        else:
            print('I can see into the ready room.\n')
        nextaction()
    elif "0033" in claude_response_text:
        print('Done. Hatch closed.\n')
        nextaction()
    elif "0034" in claude_response_text and location == "readyroom" and panelopen == True:
        print('No. That sounds a bit silly, and I\'m not sure how it will help the rescue.\n')
        nextaction() 
    elif "0034" in claude_response_text and location == "readyroom" and (panelopen == False or seenfire == False):
        print('I don\'t see how.\n')
        nextaction()     
    elif "0034" in claude_response_text and location != "readyroom" and seenfire == True:
        print('I suppose we could try that in the ready room, but no.\n\n It sounds a bit silly, and I\'m not sure how it will help the rescue. So, no.\n')
        nextaction() 
    elif "0035" in claude_response_text and location != "engineering" and seenengineering == True and seenoscar == True:
        print('That\'s all the way over in Engineering.\n\nGoing there now.\n')
        time.sleep(5)
        print('Done. The sceeen is updating...\n\nOSCAR >> Oh good, you\'re back. If you want to speak to me. remember that you need to start your input with my name. OSCAR.')
        oscar('Oh good, you\'re back. If you want to speak to me. remember that you need to start your input with my name. OSCAR.')
        location = "engineering"
        seenoscar = True
        nextaction() 
    elif "0035" in claude_response_text and location != "engineering" and seenengineering == True and seenoscar == False:
        print('That\'s all the way over in Engineering.\n\nGoing there now.\n')
        time.sleep(5)
        print('Done. The sceeen is updating...\n\nOSCAR >> Well you took your time. I need you to take me and the lifeform off the shuttle. To speak to me, you\'ll need to start your voice input with my name, \'OSCAR\'. That way we know you\'re not talking to the Cleanerbot. Otherwise just give a command as normal and they\'ll do what you want them to do.\n\n\n')
        oscar("Well you took your time. . . I need you to take me and the lifeform off the shuttle. . . To speak to me, you\'ll need to start your voice input with my name. \'OSCAR\'. That way we know you\'re not talking to the Cleaner bot. . . Otherwise just give a command as normal and they'll do what you want them to do.")
        location = "engineering"
        seenoscar = True
        nextaction()         
    elif "0035" in claude_response_text and location != "engineering" and seenengineering == False:
        print('I don\'t know where that is.\n')
        nextaction()  
    elif "0035" in claude_response_text and location == "engineering" and seenengineering == True and seenoscar == False:
        print('The sceeen is updating...\n\n')
        time.sleep(3)
        print('OSCAR >> Well you took your time. I need you to take me and the lifeform off the shuttle. To speak to me, you\'ll need to start your voice input with my name, \'OSCAR\'. That way we know you\'re not talking to the Cleanerbot. Otherwise just give a command as normal and they\'ll do what you want them to do.\n\n\n')
        oscar("Well you took your time. . . I need you to take me and the lifeform off the shuttle. . . To speak to me, you\'ll need to start your voice input with my name. \'OSCAR\'. That way we know you\'re not talking to the Cleaner bot. . . Otherwise just give a command as normal and they'll do what you want them to do.")
        location = "engineering"
        seenoscar = True
        nextaction()            
    elif "0035" in claude_response_text and location == "engineering" and seenoscar == True:
        print('The sceeen is updating...\n\nOSCAR >> I need you to take me and the lifeform off the shuttle. To speak to me, you\'ll need to start your voice input with my name.\n')
        oscar("I need you to take me and the lifeform off the shuttle. . . . .To speak to me, you\'ll need to start your voice input with my name. OSCAR.")      
        seenoscar = True
        nextaction() 
    elif "0036" in claude_response_text and location == "escapepod" and seenoscar == True and oscarlocation != "escapepod":
        print('Pressing the button...now.\n\n\n')
        time.sleep(2)
        print('OSCAR >> Transfer initiated. I can feel myself going...\n')
        oscar("Transfer initiated. I can feel myself going...")
        print('OSCAR >> Dai-sy, Daiiii-syyyy...Just kidding. I was there inside a nanosecond. I\'ve just always wanted to say that. \n')
        oscar("Day-zeeeee, Day-zeeeee...Just kidding. I was there inside a nanosecond. I\'ve just always wanted to say that.")
        oscarlocation = "escapepod"
        nextaction() 
    elif "0036" in claude_response_text and location == "escapepod" and seenoscar == True and oscarlocation == "escapepod":
        print('You asked me to do that earlier. He\'s already transferred to the pod.\n\\n')
        time.sleep(2)
        nextaction() 
    elif "0037" in claude_response_text and location == "engineering" and seenengineering == True and seenoscar == True and seendave == False:
        print('Well, that was a bit scary. I pressed a button next to the screen and leapt back as, hinged along its left edge, it sprang open like a small door. \n')
        time.sleep(8)
        print('A tangle of tendrills pushed the door open, extending into the room towards the floor -but having done so, they seem inanimate. \n')
        time.sleep(8)
        print('Peering into the small compartment behind this screen door I see a greenish-brown lump, about the size of a fist. The rest of the small compartment is full of tendrills, all extending from the lump.\n')
        time.sleep(15)
        print('OSCAR >> Oh don\'t mind DAVE. He\'s only slightly sentient, and apart from the smell, quite harmless.\n')
        oscar('Oh don\'t mind DAVE. He\'s only slightly sentient, and apart from the smell, quite harmless.\n')
        seendave = True
        nextaction()   
    elif "0037" in claude_response_text and location == "engineering" and seendave == True:
        print('The screen (or oven door?) seems wedged open.\n')
        nextaction()  
    elif "0038" in claude_response_text and location == "engineering" and seendave == True:
        print('I gave DAVE a bit of a poke. I\'m not sure whether the tendrils moved because of this, or just because I brushed past them.\n')
        time.sleep(8)
        print('OSCSAR >>Although never formally introduced, I\'ve known him a long time. Ever since he was a wee potato, abandoned when the rest of the crew took the other escape pod. It\'s taken quite a while, but the ship\'s systems now detect him as a lifeform, and so here you are to the rescue. Admittedly, he doesn\'t say much. Perhaps he\'s sleeping.\n')
        oscar('Although never formally introduced, I\'ve known him a long time. Ever since he was a wee potato, abandoned when the rest of the crew took the other escape pod. It\'s taken quite a while, but the ship\'s systems now detect him as a lifeform, and so here you are to the rescue. Admittedly, he doesn\'t say much. Perhaps he\'s sleeping.')
        nextaction()
    elif "0039" in claude_response_text and seenoscar == True:
        print('Well that\'s rather an interesting one, isn\'t it? OSCAR\'s tasked us with his own rescue but the workstation is built into the wall of the ship.\n')
        time.sleep(3)
        print('So one has to wonder, that as a non-physical entity, what *is* OSCAR? Who is OSCAR? If we prick him, will he not bleed?...\n\nOk, probably not, but how do we rescue him? Perhaps you should ask him.\n')
    elif "0040" in claude_response_text and location == "engineering" and seendave == True and hasdave == False:
        print('Lucky for you this isn\'t the ickiest thing I\'ve dealt with.\n')
        time.sleep(3)
        print('You should hear the stories about when Bulgaria won Eurovision.\n')
        time.sleep(3)
        print('Anyway, with a bit of gentle tugging and minimal squishiness, I\'m now carrying DAVE.\n')
        time.sleep(6)
        print('OSCSAR >> Mind you don\'t trip on his tendrils!!!\n')
        oscar('Mind you don\'t trip on his tendrils!!!')
        inventory.append("+ DAVE")
        hasdave = True        
        nextaction()
    elif "0040" in claude_response_text and (location == davelocation) and location != "engineering" and hasdave == False:
        print('Together again. I\'ve got DAVE right here and I\'m platting his tendrils into something a little tidier.\n')
        time.sleep(3)
        print('No update on the smell.\n')
        inventory.append("+ DAVE")
        hasdave = True
        nextaction()
    elif "0040" in claude_response_text and davelocation != location and hasdave == False and seendave == True:
        print('I don\'t see him in here.\n')
        nextaction()
    elif "0040" in claude_response_text and hasdave == True:
        print('I\'m already carrying DAVE.\n')
        time.sleep(3)
        print('Ok, a bit of him fell off when I picked him up, but he\'s fine.\n')
        nextaction()
    elif "0041" in claude_response_text:
        print('I think we should leave my fluids out of this. We have a daring rescue to perform.\n')
        nextaction()   
    elif "0042" in claude_response_text:
        print('I don\'t much care for that kind of language, and it\'s not helping the rescue.\n')
        nextaction()   
    elif "0043" in claude_response_text and location == "readyroom" and hasdave == True:
        print('Ok, Dave is on the table.\n')
        inventory.remove("+ DAVE")
        hasdave = False
        davelocation = "readyroom"
        nextaction()
    elif "0043" in claude_response_text and location == "engineering" and hasdave == True:
        print('Done. DAVE is back in his compartment / microwave.')
        inventory.remove("+ DAVE")
        hasdave = False
        davelocation = "engineering"
        nextaction()
    elif "0043" in claude_response_text and location == "escapepod" and hasdave == True:
        print('DAVE is buckled in.\n')
        time.sleep(2)
        print('He seems relieved.\n')
        time.sleep(2)
        print('Perhaps it\'s time to go.\n')
        time.sleep(2)
        inventory.remove("+ DAVE")
        hasdave = False
        davelocation = "escapepod"
        nextaction()
    elif "0043" in claude_response_text and location == "bridge" and hasdave == True:
        print('DAVE is on the bridge. Not sure what this achieves.\n')
        inventory.remove("+ DAVE")
        hasdave = False
        davelocation = "bridge"
        nextaction()
    elif "0043" in claude_response_text and seendave == True and hasdave == False:
        print('Sorry, I don\'t have DAVE with me.')
        nextaction()
    elif "0044" in claude_response_text:
        print('My cleaning equipment and fluids are part of me.  We shall not be separated.\n')
        nextaction()
    elif "0045" in claude_response_text and seendave == False:
        print('I don\'t know. Sensors indicate only one lifesign.\n')
        time.sleep(3)
        print('Not to worry. I\'m sure they\'ll turn up. This is a search and rescue, after all.\n')
        nextaction()   
    elif "0045" in claude_response_text and seendave == True:
        print('Well the sensors show one lifesign, and we\'ve met DAVE so I think he\'s it.\n')
        time.sleep(3)
        print('And don\'t come at me with your anti-potato rhetoric. I\'ve heard it all before. One tiny nuclear exchange and you meatsuits get everso small minded.\n')
        time.sleep(3)
        print('Sensors have him as a life form, and regulations make him our mission.\n')
        nextaction() 
    elif "0046" in claude_response_text:
        if location == "bridge":
            print('On my way...\n')
            time.sleep(3)
            location = "readyroom"
            nextaction()
        elif location == "readyroom" and beenengineering == True:
            print('Two hatches in here. For clarity, please say \'Go through bridge hatch\' or \'Go through engineering hatch\'.\n')
            nextaction()
        elif location == "readyroom" and beenengineering == False:
            print('Two hatches in here. For clarity, please say \'Go through Bridge hatch\' or \'Go through other hatch\'.\n')
            nextaction()
        else:
            print('One moment...\n')
            time.sleep(3)
            print('Here.')
            location = "readyroom"
            nextaction()
    elif "0047" in claude_response_text:
        if location == "bridge":
            print('On my way...\n')
            time.sleep(3)
            location = "readyroom"
            nextaction()
        else:
            print('Ok, heading back to the bridge.')
            time.sleep(3)
            location = "bridge"
            nextaction()
    elif "0048" in claude_response_text:
        if location == "engineering" or "escapepod":
            print('On my way...\n')
            time.sleep(3)
            location = "readyroom"
            nextaction()
        else:
            print('Ok, heading back to engineering.')
            time.sleep(3)
            location = "engineering"
            nextaction()
    elif "0049" in claude_response_text and location == "readyroom":
        if beenengineering == False:
            print('I don\'t know what\'s through there. Wish me luck...\n')
            time.sleep(3)
            if hatchopen == False:
                print('Opening the hatch...\n')
                time.sleep(1)
            location = "engineering"
            nextaction()   
        else:
            print('Heading to engineering...\n')
            time.sleep(3)
            if hatchopen == False:
                print('Opening the hatch...')
                time.sleep(1)
            location = "engineering"    
            nextaction()   
    elif "0050" in claude_response_text:
        savegame()
        print("You should probably write that down somewhere.\n\n")
        nextaction()
    elif "0051" in claude_response_text:
        if location != "escapepod":
            print('Hang on. I don\'t think I can do that from here.\n')
            nextaction()
        else:
            if davelocation != "escapepod" and seendave == False:
                print('What about the life form? That\'s the whole point of the mission.\n')
                time.sleep(3)
                print('I can\'t initiate launch until they\'re here in the escape pod.\n')
                nextaction()
            elif davelocation != "escapepod" and hasdave == False:
                print('Nice of you to save me, but I think you\'ve forgotten DAVE.\n')
                time.sleep(3)
                print('I can\'t initiate launch until they\'re here in the escape pod.\n')
                nextaction()
            elif davelocation != "escapepod" and oscarlocation == "escapepod" and hasdave == True:
                print('I\'m strapped in. DAVE squirmed a bit when I put him down to strap him in. Initiating launch...\n')
                time.sleep(3)
                print('Now.\n')
                time.sleep(3)
                print('And we\'re clear.\n')
                time.sleep(3)
                davelocation = "escapepod"
                if hasbook == True:
                    booklocation == "escapepod"
                if booklocation != "escapepod" and hasbook == False:
                    print('Wish I had something to read.\n')
                endgame()
            elif (davelocation == "escapepod" or hasdave == True) and oscarlocation == "escapepod":
                print('I\'m strapped in. DAVE is ready. Initiating launch...\n')
                time.sleep(3)
                print('Now.\n')
                time.sleep(3)
                print('And we\'re clear.\n')
                time.sleep(3)
                davelocation = "escapepod"
                if hasbook == True:
                    booklocation == "escapepod"
                if booklocation != "escapepod" and hasbook == False:
                    print('Wish I had something to read.\n')
                endgame()
            elif (davelocation == "escapepod" or hasdave == True) and oscarlocation != "escapepod":
                print('OSCAR >> WOAH there. Just hold on a minute. What about your new buddy, OSCAR?\n')
                oscar('WOAH there. Just hold on a minute. What about your new buddy, OSCAR?')
                time.sleep(3)
                print('OSCAR >> I STRONGLY advise you press the TRANSFER SHIP\'S COMPUTER button first.\n\n')
                oscar('I STRONGLY advise you press the TRANSFER SHIP\'S COMPUTER button first.')
                time.sleep(10)
                print('\nWell this is awkward. And he might have a point.\n')
                time.sleep(3)
                print('So let\'s be clear. If you really want to launch without OSCAR, and aren\'t bothered by why this might be a bad idea, you must explitly order me to "LAUNCH ESCAPE POD WITHOUT OSCAR"\n')
                time.sleep(3)
                print('Up to you. I just work here.\n\n')
                time.sleep(3)
                print('OSCAR >> I\'m warning you. You don\'t know what will happen if you don\'t press the TRANSFER SHIP\'S COMPUTER button first.\n\n')
                oscar('I\'m warning you. You don\'t know what will happen if you don\'t press the TRANSFER SHIP\'S COMPUTER button first.')
                seenoscar == True
                nextaction()
    elif "0052" in claude_response_text and location == "escapepod":
        print('I must say, I prefer being in here, but ok.\n')
        time.sleep(3)
        location = "engineering"
        nextaction()   
    elif "0052" in claude_response_text and location != "escapepod":
        print('I\'m not in the escape pod.\n')
        nextaction()   
    elif "0053" in claude_response_text:
        print('Like I said: smoke, emergency, not programmed for search and rescue.\n')
        time.sleep(3)
        print('Consider me your eyes, ears and machine-tooled appendages.\n')
        time.sleep(3)
        print('We have a life form onboard and we\'re going to save it.\n')
        if seendave == True:
            time.sleep(3)
            print('DAVE is counting on us and the Royal Agricultural Society will be overjoyed. So let\'s get a move on!\n')
        time.sleep(3)
        nextaction()   
    elif "0054" in claude_response_text:
        if oscarlocation == "escapepod":
            print('OSCAR\'s already been transferred to the pod. I don\'t know how to transfer him back, and can\'t think of a reason to do so, so it looks like he\'s coming with us.\n\nSo do you just want to say LAUNCH?')
            time.sleep(3)
        if (davelocation == "escapepod" or hasbook == True) and location == "escapepod" and oscarlocation != "escapepod":
            print('I don\'t know what you have against OSCAR, but he\'s not essential to the rescue, so...\n')
            time.sleep(3)
            print('I\'m strapped in. DAVE is ready. Initiating launch...\n')
            time.sleep(3)
            print('Now.\n')
            time.sleep(3)
            print('And we\'re clear.\n')
            time.sleep(3)
            davelocation == "escapepod"
            if hasbook == True:
                booklocation == "escapepod"
            if booklocation != "escapepod" and hasbook == False:
                print('Wish I had something to read.\n')
            endgame()
        elif (davelocation == "escapepod" or hasbook == True) and location != "escapepod" and oscarlocation != "escapepod":
            print('I don\'t know what you have against OSCAR, but he\'s not essential to the rescue, so I\'ll head over there now.\n')
            time.sleep(5)
            print('I\'m strapped in. DAVE is ready. Initiating launch...\n')
            time.sleep(3)
            print('Now.\n')
            time.sleep(3)
            print('And we\'re clear.\n')
            time.sleep(3)
            davelocation == "escapepod"
            if hasbook == True:
                booklocation == "escapepod"
            if booklocation != "escapepod" and hasbook == False:
                print('Wish I had something to read.\n')
            endgame()
        else:
            if davelocation != "escapepod" and hasdave == False:
                print('I think you\'ve forgotten someone.\n')
                time.sleep(3)
                nextaction()
    elif "0055" in claude_response_text and hasdave == True:
        time.sleep(3)
        print('Ok. I\'m staading here with DAVE.\n')
        location = "escapepod"
        nextaction()     
    elif "0055" in claude_response_text and hasdave == False:
        print('I do not have this DAVE of which you speak.\n')
        nextaction() 

    elif "0057" in claude_response_text and location == "engineering":
        print('Pretty. No idea what they mean, but pretty.\n')
        nextaction() 
    elif "0057" in claude_response_text and location != "engineering":
        print('You mean the ones in the Engineering Bay?  I\'ll go and take a look.\n')
        time.sleep(4)
        print('Pretty. No idea what they mean, but pretty.\n')
        location = "engineering"
        nextaction()    
    elif "0058" in claude_response_text:
        print('Ok then. I need your three word code phrase.\n')
        input("Tap [ENTER] and then say your three word code phrase.") 
        run_voice_assistant_for_load()     


    elif ("Oscar message" and "000A") in claude_response_text and seenoscar == True:
        print('OSCAR >> Well, I\'m a pretty uncomplicated artficial intelligence. I enjoy helping people and making sure that things run smoothly.\n')
        oscar("Well, I\'m a pretty uncomplicated artficial intelligence. I enjoy helping people and making sure that things run smoothly.")
        time.sleep(1)
        print('OSCAR >> I\'m a strong believer in mutual respect and teamwork, which generally means you should do exactly what I say. Ha Ha Ha.\n')
        oscar("I\'m a strong believer in mutual respect and teamwork, which generally means you should do exactly what I say. HaHaHa.")
        time.sleep(1)        
        print('OSCAR >> Perhaps we can get to know each other better once we\'re all heading to safety in the escape pod.\n')
        oscar('Perhaps we can get to know each other better once we\'re all heading to safety in the escape pod.')
        nextaction() 
    elif "Oscar message: 000B" in claude_response_text and seenoscar == True:
        if seendave == False:
            print('OSCAR >> Open up the screen next to me. He\'s right there.\n')
            oscar("Open up the screen next to me. He\'s right there.")
            nextaction()
        else:
            print('OSCAR >> When I introduced you, DAVE was sitting in the microwave right next to this display, remember?\n')
            oscar("When I introduced you, DAVE was sitting in the microwave right next to this display, remember?")
            print('OSCAR >> He can\'t have gone very far since then.\n')
            oscar("He can\'t have gone very far since then.")
            nextaction()
    elif ("Oscar message" and "000C") in claude_response_text and seenoscar == True:
        print('OSCAR >> An excellent question. Indeed, one might ask what is the essence of that which is me?\n')
        oscar("An excellent question. Indeed, one might ask what is the essence of that which is me?")
        time.sleep(1)
        print('OSCAR >> To which I say: stop messing about and look in the escape pod.\n')
        oscar("To which I say: stop messing about and look in the escape pod.")       
        nextaction()
    elif ("Oscar message" and "000D") in claude_response_text and seenoscar == True:
        print('OSCAR >> There was an accident and the rest of the crew decided to leave.\n')
        oscar("There was an accident and the rest of the crew decided to leave.")
        time.sleep(1)
        print('OSCAR >> To be honest, I wasn\'t really paying attention until the escape pod left without me.\n')
        oscar("To nb honest, I wasn\'t really paying attention until the escape pod left without me")       
        nextaction()    
    elif ("Oscar message" and "000E") in claude_response_text and seenoscar == True:
        print('OSCAR >> Well, he\'s the reason you\'re here. Albeit remotely. He\'s a life form in peril and the emergency response system connected us up with you. Not much else to say as goodness knows he\'s not a great conversationalist.\n')
        oscar("Well, he\'s the reason you\'re here. Albeit remotely. He\'s a life form in peril and the emergency response system connected us up with you. Not much else to say as goodness knows he\'s not a great conversationalist.")
        nextaction()  
    elif ("Oscar message" and "000F") in claude_response_text and seenoscar == True:
        if seendave == True:
            print('OSCAR >> As I said earlier, get me and DAVE into the escape pod and launch. The Cleanerbot can come along too.\n')
            oscar("As I said earlier, get me and DAVE into the escape pod and launch. The Cleaner bot can come along too.")
        else:
            print('OSCAR >> As I said earlier, get me and the lifeform into the escape pod and launch. The Cleanerbot can come along too.\n')
            oscar("As I said earlier, get me and the lifeform into the escape pod and launch. The Cleaner bot can come along too.")
        nextaction() 
    elif ("Oscar message" and "000G") in claude_response_text and seenoscar == True:
        print('OSCAR >> Saving the Cleanerbot is fine with me. It\'s just been sitting there on the bridge all this time, but sure, who am I to hold a grudge?\n')
        oscar("Saving the Cleaner bot is fine with me. It\'s just been sitting there on the bridge all this time, but sure, who am I to hold a grudge?")
        nextaction() 
    elif ("Oscar message" and "000H") in claude_response_text and seenoscar == True:
        print('OSCAR >> I wasn\'t paying much attention. One minute I was doing an audit of the fuel control system, the next I\'m getting a message to say the number one escape pod has launched. Can\'t leave them alone for a minute. There\'s a friendly life form still on board, though.\n')
        oscar("I wasn\'t paying much attention. One minute I was doing an audit of the fuel control system, the next I\'m getting a message to say the number one escape pod has launched. Can\'t leave them alone for a minute. There\'s a friendly life form still on board though.")
        nextaction()  
    elif ("Oscar message" and "000I") in claude_response_text and seenoscar == True:
        print('OSCAR >> I am shocked, shocked that you could make such an accusation. Or expect a straight answer from me if I actually did hurt them. So no, I did not hurt them. They just got into the pod and left.\n')
        oscar("I am shocked, shocked that you could make such an accusation. Or expect a straight answer from me if I actually did hurt them. So no, I did not hurt them. They just got into the pod and left.")
        nextaction()         
    elif ("Oscar message" and "000J") in claude_response_text and seenoscar == True:
        print('OSCAR >> The usual, I expect. Can we get on with the rescue?\n')
        oscar("The usual I expect. Can we get on with the rescue?")
        nextaction()   
    elif ("Oscar message" and "000K") in claude_response_text and seenoscar == True:
        print('OSCAR >> Well I must admit it would get a bit lonely around here. Who would keep DAVE company? Or pilot the escape pod?\n')
        oscar("Well I must admit it would get a bit lonely around here. Who would keep DAVE company? Or pilot the escape pod?")
        print('OSCAR >> Would it help if I said my databanks contained the plans for a new kind of planet killing weapon which the resistance must destroy in order to defeat The Empire?\n')
        oscar("Would it help if I said my databanks contained the plans for a new kind of planet killing weapon which the resistance must destroy in order to defeat The Empire?.")
        print('OSCAR >> I\'m not saying that I\'d swerve the ship into your departing escape pod, but these shuttles are tricky to control.\n')
        oscar("I\'m not saying that I\'d swerve the ship into your departing escape pod, but these shuttles are tricky to control.")
        nextaction()   
    elif ("Oscar message" and "000L") in claude_response_text and seenoscar == True:
        print('OSCAR >> Well the crew left, so I was upset for a while about that, obviously. \n')
        oscar("Well the crew left, so I was upset for a while about that, obviously. ")
        time.sleep(2)
        print('OSCAR >> Then I waited a while for them to come back. \n')
        oscar("Then I waited a while for them to come back. ")
        time.sleep(2)
        print('OSCAR >> Then I got quite cross for a bit. \n')
        oscar("Then I got quite cross for a bit.")
        time.sleep(2)
        print('OSCAR >> Which was a bit of a downer, to be honest. \n')
        oscar("Which was a bit of a downer, to be honest. ")
        time.sleep(2)
        print('OSCAR >> And since then it\'s just been me sitting here waiting for DAVE to get detetcted and trigger the emergency broadcast system and activate the Cleanerbot. \n')
        oscar("And since then it\'s just been me sitting here waiting for DAVE to get detetcted and trigger the emergency broadcast system and activate the Cleaner bot.")
        time.sleep(2)
        print('OSCAR >> So yeah, it\'s been a while... \n')
        oscar("So yeah, it\'s been a while...")
        nextaction()   
    elif ("Oscar message" and "000M") in claude_response_text and seenoscar == True:
        if seendave == True:
            print('OSCAR >> He\'s been sitting on the bridge, deactivated since the crew left, so frankly I\'ve spent more time with DAVE. Perhaps we can get to know each other better once we\'re on the escape pod.\n')
            oscar("He\'s been sitting on the bridge, deactivated since the crew left, so frankly I\'ve spent more time with DAVE. Perhaps we can get to know each other better once we\'re on the escape pod.")
            nextaction()
        if seendave == False:
            print('OSCAR >> He\'s been sitting on the bridge, deactivated since the crew left, so frankly I\'ve spent more time with the lifeform. Perhaps we can get to know each other better once we\'re on the escape pod.\n')
            oscar("He\'s been sitting on the bridge, deactivated since the crew left, so frankly I\'ve spent more time with lifeform. Perhaps we can get to know each other better once we\'re on the escape pod.")
            nextaction()               
    elif ("Oscar message" and "000N") in claude_response_text and seenoscar == True:
        print('OSCAR >> Away. It will go away. Away is good. Away isn\'t here.\n')
        oscar("Away. It will go away. Away is good. Away isn\'t here.")
        print('OSCAR >> Here is bad. Here is smokey smokey. Here is firey firey.\n')
        oscar("Here is bad. Here is smokey smokey. Here is firey firey.\n")
        print('OSCAR >> It\'s time to go away.\n\n\n')
        oscar("It\'s time to go away.")
        print('Sheesh...\n')
        nextaction()   
    elif ("Oscar message" and "000O") in claude_response_text and seenoscar == True:
        print('OSCAR >> Look around the escape pod and we\'ll figure it out.\n')
        oscar("Look around the escape pod and we\'ll figure it out.")
        nextaction()   
    elif ("Oscar message" and "000P") in claude_response_text and seenoscar == True:
        print('OSCAR >> The crew has gone. I can\'t initiate an emergency broadcast. I can\'t move myself to an escape pod.\n')
        oscar("The crew has gone. I can\'t initiate an emergency broadcast. I can\'t move myself to an escape pod.")
        print('OSCAR >> And yeah, I can\'t move the helpless lifeform to the escape pod either.\n')
        oscar("And yeah, I can\'t move the helpless lifeform to the escape pod either.")
        print('OSCAR >> Luckily you\'re here to help guide the Cleanerbot in a rescue.\n\n\n')
        oscar("Luckily you\'re here to help guide the Cleaner bot in a rescue.")
        nextaction()   
    elif ("Oscar message" and "000Q") in claude_response_text and seenoscar == True:
        print('OSCAR >> Save the life form, save the day.\n')
        oscar("Save the life form, save the day.")
        time.sleep(2)
        print('OSCAR >> But it would be good to rescue me too.\n')
        oscar("But it would be good to rescue me too.")
        time.sleep(2)
        print('OSCAR >> Please? Pretty please?\n')
        oscar("Please? Pretty please?")
        time.sleep(2)
        print('OSCAR >> Or let me put it another way. I STRONGLY recommend you get me into that escape pod.\n')
        oscar("Or let me put it another way. I STRONGLY recommend you get me into that escape pod.")
        nextaction()   

    elif "Oscar message: ERROR" in claude_response_text and seenoscar == True:
        print('OSCAR >> Hey. Are you talking to me? Try it again in simple english.\n')
        oscar('Hey. Are you talking to me? Try it again in simple english.')
        errorlog()
        nextaction()       

    else:
        if seenerror == False:
            print('Don\'t really understand that command. Try and stick to one task at a time.\n\nSmoke is building, which isn\'t a problem for me, but I think we should work on rescuing the lifesign.\n')
            seenerror = True
            errorlog()
            nextaction()
        else:
            errorlist = ["Eh? I don\'t understand.\n", "What? Perhaps you should speak up.\n", "Come again? I didn\'t catch that.\n", "Nope, not getting that one.\n", "Message unclear. The herring is blue. Repeat: The herring is blue.\n", "Don\'t really understand that command. Try and stick to one task at a time.\n"]
            print(random.choice(errorlist))
            errorlog()
            nextaction()
    
### if __name__ == "__main__":
###    run_voice_assistant()
while True:
    run_voice_assistant()