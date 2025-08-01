import os
import torch
import demucs.api
from pathlib import Path
import torchaudio

def check_cuda_status():
    """
    Check CUDA availability and configuration.
    """
    print("\n=== CUDA Status ===")
    print(f"CUDA is available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"Current CUDA device: {torch.cuda.current_device()}")
        print(f"Device name: {torch.cuda.get_device_name(0)}")
        print(f"Device count: {torch.cuda.device_count()}")
        print(f"Memory allocated: {torch.cuda.memory_allocated(0) / 1024**2:.2f} MB")
        print(f"Memory cached: {torch.cuda.memory_reserved(0) / 1024**2:.2f} MB")
    else:
        print("CUDA is not available. PyTorch will use CPU only.")
        print("Please check if:")
        print("1. You have an NVIDIA GPU")
        print("2. NVIDIA drivers are installed")
        print("3. CUDA toolkit is installed")
        print("4. PyTorch is installed with CUDA support")
    print("==================\n")

def process_audio_demus(input_path, unique_id):
    """
    Process audio file using htdemucs model to separate vocals and accompaniment.
    
    Args:
        input_path (str): Path to the input audio file
        unique_id (str): Unique identifier for the processed files
        
    Returns:
        dict: Dictionary containing paths to the separated audio files
    """
    # Check CUDA status
    check_cuda_status()
    
    # Check if CUDA is available
    device = "cuda" if torch.cuda.is_available() else "cpu"
    #print(f"Using device: {device}")
    
    try:
        # Initialize the separator with htdemucs model
        separator = demucs.api.Separator(
            model="htdemucs",  # Using htdemucs model which is the most reliable
            device=device,
            progress=True
        )
        
        # Convert input path to Path object
        input_path = Path(input_path)
        
        # Create output directory
        output_dir = os.path.join('static', 'uploads', unique_id)
        os.makedirs(output_dir, exist_ok=True)

        # Get original filename without extension
        original_filename = os.path.splitext(os.path.basename(input_path))[0]

        # Save separated tracks with unique_id prefix
        vocals_path = os.path.join(output_dir, f"{original_filename}_vocals.wav")
        accompaniment_path = os.path.join(output_dir, f"{original_filename}_accompaniment.wav")
        
        # Separate the audio using separate_audio_file
        separated = separator.separate_audio_file(input_path)
        original_wav, separated_tracks = separated
        
        # Save vocals
        torchaudio.save(
            vocals_path,
            separated_tracks['vocals'].cpu(),
            separator.samplerate
        )
        
        # Combine all other tracks for accompaniment
        accompaniment = torch.zeros_like(separated_tracks['vocals'])
        for source, track in separated_tracks.items():
            if source != 'vocals':
                accompaniment += track
        
        # Save accompaniment
        torchaudio.save(
            accompaniment_path,
            accompaniment.cpu(),
            separator.samplerate
        )
        
        return {
            'vocals': os.path.join(unique_id, f"{original_filename}_vocals.wav"),
            'accompaniment': os.path.join(unique_id, f"{original_filename}_accompaniment.wav")
        }
        
    except Exception as e:
        print(f"Error processing audio: {str(e)}")
        raise 