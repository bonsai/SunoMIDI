import requests
import json
from typing import Optional, Dict, Any
from pathlib import Path
import time


class SunoMIDIUploader:
    """
    Suno AI API for uploading MIDI files and generating music
    """
    
    def __init__(self, api_key: str, base_url: str = "https://api.suno.ai/v1"):
        """
        Initialize the Suno MIDI uploader
        
        Args:
            api_key: Your Suno API key
            base_url: Base URL for Suno API (default: https://api.suno.ai/v1)
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def upload_midi(self, midi_path: str, title: Optional[str] = None, 
                   style: Optional[str] = None, tags: Optional[list] = None) -> Dict[str, Any]:
        """
        Upload a MIDI file to Suno AI
        
        Args:
            midi_path: Path to the MIDI file
            title: Optional title for the generated music
            style: Optional music style/genre
            tags: Optional list of tags
            
        Returns:
            Dict containing upload response with job_id
        """
        midi_file = Path(midi_path)
        
        if not midi_file.exists():
            raise FileNotFoundError(f"MIDI file not found: {midi_path}")
        
        if not midi_file.suffix.lower() in ['.mid', '.midi']:
            raise ValueError("File must be a MIDI file (.mid or .midi)")
        
        # Read MIDI file as binary
        with open(midi_file, 'rb') as f:
            midi_data = f.read()
        
        # Prepare the upload request
        files = {
            'midi_file': (midi_file.name, midi_data, 'audio/midi')
        }
        
        data = {}
        if title:
            data['title'] = title
        if style:
            data['style'] = style
        if tags:
            data['tags'] = json.dumps(tags)
        
        # Upload endpoint
        upload_url = f"{self.base_url}/uploads/midi"
        
        # Remove Content-Type from headers for multipart upload
        upload_headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        response = requests.post(
            upload_url,
            headers=upload_headers,
            files=files,
            data=data
        )
        
        if response.status_code != 200:
            raise Exception(f"Upload failed: {response.status_code} - {response.text}")
        
        return response.json()
    
    def generate_from_midi(self, midi_path: str, prompt: Optional[str] = None,
                          style: str = "pop", duration: int = 180) -> Dict[str, Any]:
        """
        Generate music from MIDI file with additional parameters
        
        Args:
            midi_path: Path to the MIDI file
            prompt: Text prompt to guide generation
            style: Music style (pop, rock, jazz, classical, etc.)
            duration: Target duration in seconds
            
        Returns:
            Dict containing generation job details
        """
        # First upload the MIDI
        upload_result = self.upload_midi(midi_path)
        midi_id = upload_result.get('midi_id')
        
        # Generate music from uploaded MIDI
        generate_url = f"{self.base_url}/generate"
        
        payload = {
            "midi_id": midi_id,
            "style": style,
            "duration": duration
        }
        
        if prompt:
            payload["prompt"] = prompt
        
        response = requests.post(
            generate_url,
            headers=self.headers,
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Generation failed: {response.status_code} - {response.text}")
        
        return response.json()
    
    def get_generation_status(self, job_id: str) -> Dict[str, Any]:
        """
        Check the status of a generation job
        
        Args:
            job_id: The job ID returned from generate_from_midi
            
        Returns:
            Dict containing job status and result URL if complete
        """
        status_url = f"{self.base_url}/generations/{job_id}"
        
        response = requests.get(status_url, headers=self.headers)
        
        if response.status_code != 200:
            raise Exception(f"Status check failed: {response.status_code} - {response.text}")
        
        return response.json()
    
    def wait_for_completion(self, job_id: str, timeout: int = 300, 
                           poll_interval: int = 5) -> Dict[str, Any]:
        """
        Wait for a generation job to complete
        
        Args:
            job_id: The job ID to wait for
            timeout: Maximum time to wait in seconds
            poll_interval: Time between status checks in seconds
            
        Returns:
            Dict containing final job result
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_generation_status(job_id)
            
            if status.get('status') == 'completed':
                return status
            elif status.get('status') == 'failed':
                raise Exception(f"Generation failed: {status.get('error')}")
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Generation did not complete within {timeout} seconds")
    
    def download_result(self, result_url: str, output_path: str) -> None:
        """
        Download the generated audio file
        
        Args:
            result_url: URL of the generated audio
            output_path: Path to save the downloaded file
        """
        response = requests.get(result_url, stream=True)
        
        if response.status_code != 200:
            raise Exception(f"Download failed: {response.status_code}")
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)


# Example usage
if __name__ == "__main__":
    # Initialize the uploader with your API key
    api_key = "your_suno_api_key_here"
    uploader = SunoMIDIUploader(api_key)
    
    try:
        # Upload and generate music from MIDI
        print("Uploading MIDI and generating music...")
        result = uploader.generate_from_midi(
            midi_path="path/to/your/file.mid",
            prompt="Energetic electronic dance music with heavy bass",
            style="edm",
            duration=180
        )
        
        job_id = result.get('job_id')
        print(f"Generation started. Job ID: {job_id}")
        
        # Wait for completion
        print("Waiting for generation to complete...")
        final_result = uploader.wait_for_completion(job_id)
        
        # Download the result
        audio_url = final_result.get('audio_url')
        print(f"Generation complete! Downloading from: {audio_url}")
        
        uploader.download_result(audio_url, "output.mp3")
        print("Download complete! Saved to output.mp3")
        
    except Exception as e:
        print(f"Error: {e}")
