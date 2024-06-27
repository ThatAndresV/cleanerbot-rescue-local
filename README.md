# cleanerbot-rescue-local
A rough and ready codebase to get you AI-powered, voice-driven text adventure running on your local machine.

One of the things that drove me crazy about text adventure games when I was a kid was intention. Matching what I want my character to do to however the developer thought they should describe it: "Get the book" vs "Take the book" vs "Grab the book" vs "Pick up the book".

Can cheap, fast, Natural Language Processing help fix that? Could I find out without building just another chatbot?

Well, yeah -here's the code. And I even wrote about:

 - [this local version you can run on your own machine](https://andresvarela.com/2024/06/cleanerbot-rescue-part-1/)
 - a web version you can [play for yourself online](https://dulcet-buttress-422311-g5.et.r.appspot.com/)
 - the codebase for that online version
 - and even a [completely codeless implementation](https://andresvarela.com/2024/06/cleanerbot-rescue-part-3/)

You (the player) are communicating remotely with a distant Cleanerbot, directing it on a search and rescue mission on a burning spaceship to excuse any latency between input and response.  You speak rather than type your inputs. This is a 21st century text adventure after all.

This Python application integrates various functionalities for audio processing, Google Cloud services, and the Anthropic API. It includes features for speech-to-text, text-to-speech, and interacting with the Claude AI model. The application is designed to handle audio input, process commands, and generate responses using AI and cloud-based services.

## Features

- **Google Cloud Speech-to-Text**: Converts audio input into text.
- **Google Cloud Text-to-Speech**: Converts text responses into spoken audio.
- **Anthropic API Integration**: Utilizes Claude AI for processing user commands and generating responses.
- **Audio Processing**: Uses PyAudio for handling audio input and output.
- **Text-to-Speech with pyttsx3**: Provides an offline alternative for text-to-speech conversion.
- **Session Management**: Includes mechanisms to handle user sessions and manage errors and profanity.

## Prerequisites

- Python 3.7+
- Google Cloud account with enabled Speech-to-Text and Text-to-Speech APIs.
- Anthropic API access.
- Required Python packages listed in `requirements.txt`.

## Setup

1. **Clone the Repository**

    ```bash
    git clone https://github.com/thatandresv/cleanerbot-rescue-local.git
    cd cleanerbot-rescue-local
    ```

2. **Create a Virtual Environment**

    - On Windows

        ```bash
        python -m venv venv
        ```
    - On macOS / Linux

        ```bash
        python3 -m venv venv
        ```    

3. **Activate the Virtual Environment**

    - On Windows:

        ```bash
        venv\Scripts\activate
        ```

    - On macOS/Linux:

        ```bash
        source venv/bin/activate
        ```

4. **Install the Required Packages**

    - On Windows: 

        ```bash
        pip install -r requirements.txt
        ```

    - On macOS:

        ```bash
        pip3 install -r requirements.txt
        ```
        If the pyaudio install failed, you have to install portaudio. The only way to do this (other than building from source) is via homebrew. Installing pyaudio via homebrew *also* requires XCode command line tools (About 1.2GB in file size.)

        First, let's install XCode CL tools:

        ```bash
        xcode-select --install
        ```
        And select **Install** on the popup.
        This will take a few minutes.

        Next, homewbew:
        ```bash
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        ```
        Other ways to install homebrew can be found at homebrew's [official website](https://brew.sh/)

        Now, portaudio:
        ```bash
        brew install portaudio
        ```

        And finally, pyaudio:
        ```bash
        pip3 install pyaudio
        ```
    - On Linux:

        Update system packages

        ```bash
        sudo apt update
        ```
        Make sure to have portaudio19-dev and python3-all-dev:

        ```bash
        apt install portaudio19-dev
        apt install python3-all-dev
        ```

        Use the package manager to install PyAudio:

        ```bash
        sudo apt install python3-pyaudio
        ```
        If something goes wrong, install it using pip:

        ```bash
        pip3 install pyaudio
        ```
        
5. **Set Up Google Cloud API Credentials**

    Ensure you have your Google Cloud credentials JSON file. Set the environment variable for Google Cloud:

    ```bash
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/to/your/credentials.json"
    ```

6. **Set Up Anthropic API Key**

    Ensure you have your Anthropic API key set in the environment variable:

    ```bash
    api_key="your_anthropic_api_key",
    ```

## Usage

1. **Run the Application**

    - On Windows

        ```bash
        python cleanerbot-rescue.py
        ```

    - On macOS/Linux:

        ```bash
        python3 cleanerbot-rescue.py
        ```

2. **Interacting with the Application**

    - The application listens for audio input, processes it, and generates responses.
    - It includes mechanisms to handle errors and provide feedback through audio.

## Additional Information

- **Configuration**: You'll need to update the file to include you API keys for Google Cloud and Anthropic (although you could easily switch to another LLM). The Google Cloud API 
transcribes the player's audio input into text, which is in turn passed to Anthopic's Claude for interpretation of player intent.
 
- **Dependencies**: The `requirements.txt` file includes all necessary Python packages. When a player saves their position in the game, they're given a unique 3-word code phrase which is recorded in the file `gamesaves.txt` with all the variables defining the player's position in the game. The three words are chosen from each of `s1.txt`, `s2.txt` and `s3.txt`. When  the player completes the game (there's more than one) they get a kind of report card of how many commands they gave Cleanerbot27 (`actioncounts.txt`) and how many times they were misunderstood (`errorcounts.txt`) in comparison to other sessions. That's a bit elaborate for a single-instance game, but I added it after I wrote the online version and wanted a way for individuals to save their game without having to register.

- **Non-dependent, irrelevant, harmless stuff**: This is the not the cleanest code you've ever seen. Not the cleanest code I've ever written. There might be a couple of functions here and there that are never called -that kind of thing. Nothing malicious - just carelessness because I'm in a hurry to move onto building [a web version that anyone can play](https://dulcet-buttress-422311-g5.et.r.appspot.com/) and [then write about it](https://andresvarela.com/#blog).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Google Cloud](https://cloud.google.com/) for their powerful APIs.
- [Anthropic](https://www.anthropic.com/) for the Claude AI model.
- [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/) for audio processing.
- [pyttsx3](https://pyttsx3.readthedocs.io/) for offline text-to-speech.

