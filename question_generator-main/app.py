"""
Flask Application for Agentic Video Question Generation Pipeline
Converts video + transcript into validated educational questions
Supports automatic transcript generation from video                logger.info(f"Using Visual-First pipeline with {len(transcript_segments)} segments")files
"""

import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from agents.pipeline import TriPlusOnePipeline
from agents.transcript_loader import TranscriptLoader
from agents.llm_judge import LLMJudge
from agents.context_validator import ContextValidator
from agents.question_generator import QuestionGenerator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Allowed file extensions
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv'}
ALLOWED_TRANSCRIPT_EXTENSIONS = {'json', 'txt', 'srt', 'vtt'}

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

def allowed_file(filename, allowed_extensions):
    """Check if uploaded file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/')
def index():
    """Home page with upload form"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle video and optional transcript file uploads"""
    try:
        # Check if video file is present
        if 'video' not in request.files:
            return jsonify({'error': 'Video file is required'}), 400
        
        video_file = request.files['video']
        transcript_file = request.files.get('transcript')  # Optional now
        
        if video_file.filename == '':
            return jsonify({'error': 'No video file selected'}), 400
        
        # Validate video file extension
        if not allowed_file(video_file.filename, ALLOWED_VIDEO_EXTENSIONS):
            return jsonify({'error': 'Invalid video file format'}), 400
        
        # Validate transcript file if provided
        if transcript_file and transcript_file.filename != '':
            if not allowed_file(transcript_file.filename, ALLOWED_TRANSCRIPT_EXTENSIONS):
                return jsonify({'error': 'Invalid transcript file format'}), 400
        
        # Save files securely
        video_filename = secure_filename(video_file.filename)
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
        video_file.save(video_path)
        
        transcript_filename = None
        if transcript_file and transcript_file.filename != '':
            transcript_filename = secure_filename(transcript_file.filename)
            transcript_path = os.path.join(app.config['UPLOAD_FOLDER'], transcript_filename)
            transcript_file.save(transcript_path)
        
        logger.info(f"Video uploaded: {video_filename}")
        if transcript_filename:
            logger.info(f"Transcript uploaded: {transcript_filename}")
        
        return jsonify({
            'message': 'Files uploaded successfully',
            'video_file': video_filename,
            'transcript_file': transcript_filename,
            'has_transcript': transcript_filename is not None
        })
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/process', methods=['POST'])
def process_video():
    """Process video and generate questions with optional transcript generation"""
    try:
        data = request.get_json()
        
        if not data or 'video_file' not in data:
            return jsonify({'error': 'Video file name is required'}), 400
        
        video_filename = data['video_file']
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
        
        if not os.path.exists(video_path):
            return jsonify({'error': 'Video file not found'}), 404
        
        # Check for transcript file or generation options
        transcript_filename = data.get('transcript_file')
        generate_transcript = data.get('generate_transcript', False)
        transcript_method = data.get('transcript_method', 'whisper')
        output_format = data.get('output_format', 'vtt')
        
        transcript_path = None
        
        # Handle transcript generation or existing file
        if generate_transcript:
            try:
                # Generate transcript using VideoTranscriptGenerator
                from agents.transcript_generator import VideoTranscriptGenerator
                
                transcript_gen = VideoTranscriptGenerator()
                
                # Generate transcript and save it
                base_name = os.path.splitext(video_filename)[0]
                transcript_filename = f"{base_name}_transcript.{output_format}"
                transcript_path = os.path.join(app.config['UPLOAD_FOLDER'], transcript_filename)
                
                # Generate transcript based on method
                if transcript_method == 'whisper':
                    transcript_data = transcript_gen.transcribe_with_whisper(video_path)
                else:
                    transcript_data = transcript_gen.transcribe_with_speech_recognition(video_path)
                
                # Save in requested format
                if output_format == 'vtt':
                    transcript_gen.save_as_vtt(transcript_data, transcript_path)
                elif output_format == 'srt':
                    transcript_gen.save_as_srt(transcript_data, transcript_path)
                else:
                    transcript_gen.save_as_json(transcript_data, transcript_path)
                
                logger.info(f"Transcript generated: {transcript_filename}")
                
            except Exception as e:
                logger.error(f"Transcript generation error: {str(e)}")
                return jsonify({'error': f'Transcript generation failed: {str(e)}'}), 500
        
        elif transcript_filename:
            # Use existing transcript file
            transcript_path = os.path.join(app.config['UPLOAD_FOLDER'], transcript_filename)
            if not os.path.exists(transcript_path):
                return jsonify({'error': 'Transcript file not found'}), 404
        else:
            return jsonify({'error': 'Either provide transcript file or enable transcript generation'}), 400
        
        # Get processing options
        num_questions = int(data.get('num_questions', 5))
        include_mcq = data.get('include_mcq', True)  # Enabled by default for enhanced types
        use_vlm = data.get('use_vlm', True)
        analysis_mode = data.get('analysis_mode', 'strategic_hybrid')  # NEW: Strategic hybrid as default
        
        logger.info(f"Processing request: {num_questions} questions, analysis_mode={analysis_mode}")
        
        # Initialize processors - Use proper pipeline approach
        try:
            # Use Visual-First Pipeline for educational content
            from agents.pipeline import TriPlusOnePipeline
            pipeline = TriPlusOnePipeline(use_vlm=use_vlm)
            
            # Load transcript segments
            if transcript_path:
                file_extension = os.path.splitext(transcript_path)[1].lower()
                if file_extension == '.docx':
                    from agents.docx_transcript_extractor import DocxTranscriptExtractor
                    docx_extractor = DocxTranscriptExtractor()
                    transcript_segments = docx_extractor.extract_transcript_from_docx(transcript_path)
                else:
                    from agents.transcript_loader import TranscriptLoader
                    transcript_loader = TranscriptLoader()
                    transcript_segments = transcript_loader.load(transcript_path)
                
                logger.info(f"� Using Visual-First pipeline with {len(transcript_segments)} segments")
                
                # Run Visual-First pipeline: Slides as primary source, transcript as context
                questions = pipeline.run(video_path, transcript_segments)
                
            else:
                logger.error("No transcript provided for visual-first analysis")
                return jsonify({'error': 'Transcript required for visual-first question generation'}), 400
            
            # Validate questions with enhanced LLM Judge
            from agents.llm_judge import LLMJudge
            judge = LLMJudge()
            
            validated_questions = []
            pipeline_context = {'summary': f'Visual-first analysis of {len(questions)} segments'}
            
            for question in questions:
                try:
                    evaluation = judge.judge_question(question['question'], pipeline_context)
                    
                    # Check if it's the new format (dict) or old format (float)
                    if isinstance(evaluation, dict):
                        score = evaluation.get('score', 0)
                        difficulty = evaluation.get('difficulty', 'medium')
                        tags = evaluation.get('tags', [])
                        cognitive_level = evaluation.get('cognitive_level', 'understand')
                        feedback = evaluation.get('feedback', '')
                    else:
                        # Old format - just a score
                        score = evaluation
                        difficulty = 'medium'
                        tags = [question['question'].get('type', 'factual')]
                        cognitive_level = 'understand'
                        feedback = ''
                    
                    # Extract VLM analysis from segment context (Visual-First approach)
                    segment_context = question.get('segment_context', {})
                    vlm_analysis = segment_context.get('vlm_analysis')
                    
                    # Format VLM analysis for output
                    if isinstance(vlm_analysis, dict):
                        vlm_analysis_str = f"Analysis method: {vlm_analysis.get('analysis_method', 'Unknown')}. " + \
                                         f"Frame analysis: {vlm_analysis.get('frame_analysis', '')}. " + \
                                         f"Educational concepts: {', '.join(vlm_analysis.get('educational_concepts', []))}"
                    else:
                        vlm_analysis_str = vlm_analysis or 'No VLM analysis available'
                    
                    if score >= 7:  # Quality threshold
                        validated_questions.append({
                            'question': question['question'],
                            'timestamp': question.get('timestamp', '00:00:00'),
                            'segment_text': segment_context.get('transcript_text', ''),
                            'quality_score': score,
                            'difficulty': difficulty,
                            'tags': tags,
                            'cognitive_level': cognitive_level,
                            'feedback': feedback,
                            'question_type': question.get('question_type', 'factual'),
                            
                            'vlm_analysis': vlm_analysis_str,
                            'transcript_analysis': segment_context.get('transcript_analysis', {}),
                            'frame_analysis_confidence': segment_context.get('confidence', 0),
                            'transcript_analysis_confidence': question.get('transcript_analysis_confidence', 0),
                            'educational_indicators': segment_context.get('educational_concepts', []),
                            'concept_extraction_method': segment_context.get('method', 'unknown'),
                            'visual_elements': ', '.join(segment_context.get('visual_elements', [])),
                            'strategic_tier': question.get('strategic_tier', 'unknown'),
                            'analysis_mode': segment_context.get('method', 'unknown')
                        })
                        
                except Exception as e:
                    logger.error(f"Error evaluating question: {e}")
                    continue
            
            # Generate output filename
            base_name = os.path.splitext(video_filename)[0]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"{base_name}_questions_{timestamp}.json"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            # Save results
            results = {
                'video_file': video_filename,
                'transcript_file': transcript_filename,
                'generated_transcript': generate_transcript,
                'processing_options': {
                    'num_questions': num_questions,
                    'include_mcq': include_mcq,
                    'use_vlm': use_vlm,
                    'analysis_mode': analysis_mode
                },
                'context_summary': f'Visual-first pipeline processed {len(questions)} questions',
                'questions': validated_questions,
                'total_questions': len(validated_questions),
                'timestamp': timestamp
            }
            
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Questions generated and saved: {output_filename}")
            
            return jsonify({
                'message': 'Video processed successfully',
                'results_file': output_filename,
                'questions_generated': len(validated_questions),
                'transcript_generated': generate_transcript,
                'download_url': f'/download/{output_filename}'
            })
            
        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            return jsonify({'error': f'Processing failed: {str(e)}'}), 500
        
    except Exception as e:
        logger.error(f"Process endpoint error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/questions')
def view_questions():
    """View generated questions"""
    return render_template('questions.html')

@app.route('/api/questions/<filename>')
def get_questions(filename):
    """API endpoint to get questions from a file"""
    try:
        # Questions are saved in OUTPUTS_FOLDER
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'Questions file not found'}), 404
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Extract just the questions array if it's wrapped in an object
        if isinstance(data, dict) and 'questions' in data:
            questions = data['questions']
        else:
            questions = data
        
        return jsonify(questions)
        
    except Exception as e:
        logger.error(f"Error loading questions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard-stats')
def dashboard_stats():
    """Get dashboard statistics"""
    try:
        # Count files in upload and output folders
        upload_files = len([f for f in os.listdir(app.config['UPLOAD_FOLDER']) 
                           if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], f))])
        
        output_files = len([f for f in os.listdir(app.config['OUTPUT_FOLDER']) 
                           if f.endswith('.json')])
        
        # Count different file types
        video_files = len([f for f in os.listdir(app.config['UPLOAD_FOLDER']) 
                          if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm'))])
        
        transcript_files = len([f for f in os.listdir(app.config['UPLOAD_FOLDER']) 
                               if f.lower().endswith(('.txt', '.vtt', '.srt', '.json'))])
        
        stats = {
            'total_uploads': upload_files,
            'video_files': video_files,
            'transcript_files': transcript_files,
            'generated_questions': output_files,
            'last_processed': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Dashboard stats error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/favicon.ico')
def favicon():
    """Handle favicon requests"""
    return '', 204

@app.route('/api/generate_transcript', methods=['POST'])
def generate_transcript():
    """Generate transcript from video file only"""
    try:
        data = request.get_json()
        
        if not data or 'video_file' not in data:
            return jsonify({'error': 'Video file name is required'}), 400
        
        video_filename = data['video_file']
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
        
        if not os.path.exists(video_path):
            return jsonify({'error': 'Video file not found'}), 404
        
        transcript_method = data.get('transcript_method', 'whisper')
        output_format = data.get('output_format', 'vtt')
        
        try:
            # Generate transcript using VideoTranscriptGenerator
            from agents.transcript_generator import VideoTranscriptGenerator
            
            transcript_gen = VideoTranscriptGenerator()
            
            # Generate transcript and save it
            base_name = os.path.splitext(video_filename)[0]
            transcript_filename = f"{base_name}_transcript.{output_format}"
            transcript_path = os.path.join(app.config['UPLOAD_FOLDER'], transcript_filename)
            
            # Generate transcript based on method
            if transcript_method == 'whisper':
                transcript_data = transcript_gen.transcribe_with_whisper(video_path)
            else:
                transcript_data = transcript_gen.transcribe_with_speech_recognition(video_path)
            
            # Save in requested format
            if output_format == 'vtt':
                transcript_gen.save_as_vtt(transcript_data, transcript_path)
            elif output_format == 'srt':
                transcript_gen.save_as_srt(transcript_data, transcript_path)
            else:
                transcript_gen.save_as_json(transcript_data, transcript_path)
            
            logger.info(f"Transcript generated: {transcript_filename}")
            
            return jsonify({
                'message': 'Transcript generated successfully',
                'transcript_file': transcript_filename,
                'method': transcript_method,
                'format': output_format
            })
            
        except Exception as e:
            logger.error(f"Transcript generation error: {str(e)}")
            return jsonify({'error': f'Transcript generation failed: {str(e)}'}), 500
        
    except Exception as e:
        logger.error(f"Generate transcript endpoint error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/files')
def list_files():
    """List available question files"""
    try:
        # Questions are saved in UPLOAD_FOLDER, so look there
        question_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) 
                         if '_questions_' in f and f.endswith('.json')]
        return jsonify({'files': question_files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/download/<filename>')
def download_file(filename):
    """Download generated questions file"""
    try:
        return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 500MB.'}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
