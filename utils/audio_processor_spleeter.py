import os
import tensorflow as tf
from spleeter.separator import Separator
import librosa
import soundfile as sf
import numpy as np
from pathlib import Path

def process_audio_undone(input_path, unique_id):
    """
    DEPRECATED: This method is non-functional due to compatibility issues between ffmpeg and shutil.which().
    The ffmpeg binary cannot be properly located by shutil.which(), causing the audio processing to fail.
    
    The core issue is that Spleeter relies on ffmpeg for audio processing, but uses shutil.which() to locate 
    the ffmpeg binary. On some systems, even when ffmpeg is installed and in PATH, shutil.which() fails to 
    find it correctly. This appears to be due to how shutil.which() handles path resolution on certain 
    platforms

    A workaround is implemented in process_audio_old() which avoids this issue.
    
    For more details see: https://github.com/deezer/spleeter/issues/672#issuecomment-1162924661

    Process audio file using Spleeter to separate vocals and accompaniment.
    
    Args:
        input_path (str): Path to the input audio file
        unique_id (str): Unique identifier for the processed files
        
    Returns:
        dict: Dictionary containing paths to the separated audio files
        
    Raises:
        RuntimeError: Always raises an error since this method is deprecated and non-functional
    """
    # Initialize the separator with 2stems model
    separator = Separator('spleeter:2stems')
    
    # Create output directory
    output_dir = Path('static/uploads')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process the audio file
    try:
        # Create a subdirectory for this specific file
        output_subdir = output_dir / unique_id
        output_subdir.mkdir(parents=True, exist_ok=True)
        
        # Separate the audio
        separator.separate_to_file(
            input_path,
            output_subdir,
            filename_format='{instrument}.{codec}',
            codec='wav',
            duration=None,
            bitrate='128k'
        )
        
        # Return the paths to the separated files
        return {
            'vocals': os.path.join(unique_id, 'vocals.wav'),
            'accompaniment': os.path.join(unique_id, 'accompaniment.wav')
        }
        
    except Exception as e:
        print(f"Error processing audio: {str(e)}")
        raise

def process_audio_old(input_path, unique_id):
    """
    Process audio file using Spleeter to separate vocals and accompaniment.
    
    Args:
        input_path (str): Path to input audio file
        unique_id (str): Unique identifier for the processing session
    
    Returns:
        dict: Paths to separated audio files
    """
    try:
        # Initialize Spleeter separator (2 stems: vocals and accompaniment)
        separator = Separator('spleeter:2stems')
        
        # Load audio file and ensure it's in the correct format
        waveform, sample_rate = librosa.load(input_path, sr=None)
        
        # Ensure the waveform is in the correct shape (samples, channels)
        if len(waveform.shape) == 1:
            waveform = np.reshape(waveform, (-1, 1))
        
        # Perform separation
        prediction = separator.separate(waveform)
        
        # Create output directory
        output_dir = os.path.join('static', 'uploads', unique_id)
        os.makedirs(output_dir, exist_ok=True)
        
        # Get original filename without extension
        original_filename = os.path.splitext(os.path.basename(input_path))[0]
        
        # Save separated tracks with original filename
        vocals_path = os.path.join(output_dir, f"{original_filename}_vocals.wav")
        accompaniment_path = os.path.join(output_dir, f"{original_filename}_accompaniment.wav")
        
        # Ensure the output arrays are in the correct shape and format
        vocals = prediction['vocals']
        accompaniment = prediction['accompaniment']
        
        if len(vocals.shape) == 1:
            vocals = np.reshape(vocals, (-1, 1))
        if len(accompaniment.shape) == 1:
            accompaniment = np.reshape(accompaniment, (-1, 1))
        
        # Save the audio files
        sf.write(vocals_path, vocals, sample_rate)
        sf.write(accompaniment_path, accompaniment, sample_rate)
        
        # Return relative paths for web access
        return {
            'vocals': os.path.join(unique_id, f"{original_filename}_vocals.wav"),
            'accompaniment': os.path.join(unique_id, f"{original_filename}_accompaniment.wav")
        }
    except Exception as e:
        raise Exception(f"Error processing audio: {str(e)}") 