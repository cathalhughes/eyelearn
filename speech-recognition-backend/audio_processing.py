import speech_recognition as sr

def get_recorder():
    recogniser = sr.Recognizer()
    return recogniser

def get_audio(filename, recogniser):
    audio = sr.AudioFile(filename)
    # with open("audio1.wav", "wb") as f:
    #     f.write(audio.write())
    with audio as source:
        recogniser.adjust_for_ambient_noise(source)
        audio = recogniser.record(source)


    return audio

def recognise_audio(audio, recogniser, recognitionLanguage):
    print("in recognise ausdio")
    response = {
        "success": True,
        "error": None,
        "transcription": None
    }

    try:
        print("try")
        response["transcription"] = recogniser.recognize_google(audio, language=recognitionLanguage)
    except sr.RequestError:
        print("except 1")
        # API was unreachable or unresponsive
        response["success"] = False
        response["error"] = "API unavailable"
    except sr.UnknownValueError:
        print("except 2 ")
        # speech was unintelligible
        response["error"] = "Unable to recognize speech"
        response["transcription"] = "Please speak more clearly"
    except TimeoutError:
        print("timeout")
        response["success"] = False
        response["error"] = "API Unavailable - Timed out!"
        response["transcription"] = "Service down, please try again later!"

    return response
