import os
from flask import Flask, request, render_template, jsonify, send_file
from utils.audio_processor_spleeter import process_audio_old
from utils.audio_processor_demucs import process_audio_demus
import uuid
import json
from datetime import datetime
import zipfile
import io
import whisper
import tempfile

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'mp3', 'wav'}
app.config['HISTORY_FILE'] = os.path.join('static', 'uploads', 'processing_history.json')
app.config['MAX_HISTORY'] = 10  # Maximum number of files to keep in history

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Whisper model
whisper_model = whisper.load_model("base")

def load_history():
    if os.path.exists(app.config['HISTORY_FILE']):
        with open(app.config['HISTORY_FILE'], 'r') as f:
            return json.load(f)
    return []

def save_history(history):
    # Keep only the most recent MAX_HISTORY items
    history = sorted(history, key=lambda x: x['upload_date'], reverse=True)[:app.config['MAX_HISTORY']]
    with open(app.config['HISTORY_FILE'], 'w') as f:
        json.dump(history, f, indent=4)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    history = load_history()
    return render_template('index.html', history=history)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Use original filename
        filename = file.filename
        unique_id = str(uuid.uuid4())
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
        file.save(file_path)
        
        # Add to history
        history = load_history()
        history.append({
            'id': unique_id,
            'original_name': filename,
            'upload_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'uploaded'
        })
        save_history(history)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'unique_id': unique_id
        })
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    if not data or 'filename' not in data or 'unique_id' not in data or 'method' not in data:
        return jsonify({'error': 'Missing required data'}), 400
    
    filename = data['filename']
    unique_id = data['unique_id']
    method = data['method']  # 'spleeter' or 'demucs'
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
    
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        # Choose the appropriate processing method
        if method == 'spleeter':
            output_paths = process_audio_old(input_path, unique_id)
        elif method == 'demucs':
            output_paths = process_audio_demus(input_path, unique_id)
        else:
            return jsonify({'error': 'Invalid separation method'}), 400

        if not output_paths or 'vocals' not in output_paths or 'accompaniment' not in output_paths:
            return jsonify({'error': 'Processing failed'}), 500
        
        # Update history
        history = load_history()
        for item in history:
            if item['id'] == unique_id:     
                item['status'] = 'processed'
                item['vocals_path'] = output_paths['vocals']
                item['accompaniment_path'] = output_paths['accompaniment']
                item['method'] = method  # Store the method used
                break
        save_history(history)
            
        return jsonify({
            'success': True,
            'vocals_path': output_paths['vocals'],
            'accompaniment_path': output_paths['accompaniment']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<path:filename>')
def download_file(filename):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
            
        return send_file(
            file_path,
            as_attachment=True
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/play/<path:filename>')
def play_file(filename):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
            
        # Determine the MIME type based on file extension
        ext = os.path.splitext(filename)[1].lower()
        mime_type = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.ogg': 'audio/ogg'
        }.get(ext, 'audio/mpeg')
            
        return send_file(
            file_path,
            mimetype=mime_type,
            as_attachment=False
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/download-all')
def download_all():
    try:
        history = load_history()
        if not history:
            return jsonify({'error': 'No files to download'}), 404

        # Create a ZIP file in memory
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for item in history:
                if item['status'] == 'processed':
                    # Add vocals
                    vocals_path = os.path.join(app.config['UPLOAD_FOLDER'], item['vocals_path'])
                    if os.path.exists(vocals_path):
                        zf.write(vocals_path, f"{item['id']}_{item['original_name']}_vocals.wav")
                    
                    # Add accompaniment
                    accompaniment_path = os.path.join(app.config['UPLOAD_FOLDER'], item['accompaniment_path'])
                    if os.path.exists(accompaniment_path):
                        zf.write(accompaniment_path, f"{item['id']}_{item['original_name']}_accompaniment.wav")

        memory_file.seek(0)
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name='all_separated_tracks.zip'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download-vocals')
def download_vocals():
    try:
        history = load_history()
        if not history:
            return jsonify({'error': 'No files to download'}), 404

        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for item in history:
                if item['status'] == 'processed':
                    vocals_path = os.path.join(app.config['UPLOAD_FOLDER'], item['vocals_path'])
                    if os.path.exists(vocals_path):
                        zf.write(vocals_path, f"{item['id']}_{item['original_name']}_vocals.wav")

        memory_file.seek(0)
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name='all_vocals.zip'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download-accompaniment')
def download_accompaniment():
    try:
        history = load_history()
        if not history:
            return jsonify({'error': 'No files to download'}), 404

        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for item in history:
                if item['status'] == 'processed':
                    accompaniment_path = os.path.join(app.config['UPLOAD_FOLDER'], item['accompaniment_path'])
                    if os.path.exists(accompaniment_path):
                        zf.write(accompaniment_path, f"{item['id']}_{item['original_name']}_accompaniment.wav")

        memory_file.seek(0)
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name='all_accompaniment.zip'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clear-history', methods=['POST'])
def clear_history():
    try:
        # Delete all processed files
        history = load_history()
        for item in history:
            if item['status'] == 'processed':
                # Delete vocals
                vocals_path = os.path.join(app.config['UPLOAD_FOLDER'], item['vocals_path'])
                if os.path.exists(vocals_path):
                    os.remove(vocals_path)
                # Delete accompaniment
                accompaniment_path = os.path.join(app.config['UPLOAD_FOLDER'], item['accompaniment_path'])
                if os.path.exists(accompaniment_path):
                    os.remove(accompaniment_path)
            # Delete original file
            original_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{item['id']}_{item['original_name']}")
            if os.path.exists(original_path):
                os.remove(original_path)
        
        # Clear history file
        save_history([])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/history')
def get_history():
    history = load_history()
    return jsonify(history)

@app.route('/transcribe', methods=['GET', 'POST'])
def transcribe():
    if request.method == 'GET':
        return render_template('transcribe.html')
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    language = request.form.get('language', 'auto')
    
    try:
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            file.save(temp_file.name)
            
            # Transcribe the audio
            result = whisper_model.transcribe(
                temp_file.name,
                language=language if language != 'auto' else None
            )
            
            # Clean up the temporary file
            os.unlink(temp_file.name)
            
            return jsonify({'text': result['text']})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 