# app.py - COMPLETE OPENAI API INTEGRATION FOR ALL FUNCTIONALITIES
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import PyPDF2
import docx
import openai
import json
import re
import logging
from datetime import datetime
from typing import Dict, List, Any

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Career configurations
CAREER_CONFIGS = {
    'fullstack': {
        'title': 'Full-Stack Developer',
        'description': 'Build complete web applications with frontend and backend technologies',
        'skills': ['JavaScript', 'React', 'Node.js', 'Database', 'APIs', 'HTML/CSS'],
        'languages': ['JavaScript', 'Python', 'SQL']
    },
    'frontend': {
        'title': 'Frontend Developer',
        'description': 'Specialize in user interface and client-side development',
        'skills': ['HTML/CSS', 'JavaScript', 'React', 'TypeScript', 'UI/UX'],
        'languages': ['JavaScript', 'TypeScript']
    },
    'backend': {
        'title': 'Backend Developer',
        'description': 'Focus on server-side logic and database management',
        'skills': ['Node.js', 'Python', 'Java', 'Database', 'APIs', 'Authentication'],
        'languages': ['JavaScript', 'Python', 'Java', 'C#']
    },
    'datascience': {
        'title': 'Data Scientist',
        'description': 'Analyze data and build machine learning models',
        'skills': ['Python', 'Statistics', 'Machine Learning', 'SQL', 'Data Visualization'],
        'languages': ['Python', 'R', 'SQL']
    },
    'machinelearning': {
        'title': 'Machine Learning Engineer',
        'description': 'Design and implement AI models and systems',
        'skills': ['Python', 'Machine Learning', 'Deep Learning', 'TensorFlow', 'Data Engineering'],
        'languages': ['Python', 'C++']
    },
    'mobile': {
        'title': 'Mobile Developer',
        'description': 'Build applications for iOS and Android platforms',
        'skills': ['React Native', 'Swift', 'Kotlin', 'Mobile UI', 'APIs'],
        'languages': ['JavaScript', 'Swift', 'Kotlin', 'Java']
    },
    'devops': {
        'title': 'DevOps Engineer',
        'description': 'Manage deployment, infrastructure, and CI/CD pipelines',
        'skills': ['Docker', 'Kubernetes', 'AWS', 'CI/CD', 'Linux'],
        'languages': ['Python', 'JavaScript', 'Bash']
    }
}


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


@app.route('/api/careers/list', methods=['GET'])
def get_career_list():
    """Get list of available careers"""
    try:
        careers = []
        for career_id, config in CAREER_CONFIGS.items():
            careers.append({
                'id': career_id,
                'name': config['title'],
                'description': config['description'],
                'average_salary_range': get_salary_range(career_id),
                'growth_outlook': get_growth_outlook(career_id),
                'key_technologies': config['skills'][:4]
            })

        return jsonify({'careers': careers})

    except Exception as e:
        logger.error(f"Career list error: {str(e)}")
        return jsonify({'error': 'Failed to load careers'}), 500


@app.route('/api/skills/analyze', methods=['POST'])
def analyze_skills():
    """AI-powered CV analysis with OpenAI"""
    try:
        logger.info("Starting AI CV analysis...")

        if 'cv' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['cv']
        target_career = request.form.get('target_career', '')

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not target_career:
            return jsonify({'error': 'No target career selected'}), 400

        logger.info(f"Processing CV for career: {target_career}")

        # Extract text from CV
        cv_text = extract_text_from_file(file)

        if not cv_text or len(cv_text.strip()) < 50:
            return jsonify({'error': 'Could not extract meaningful text from CV'}), 400

        # Generate AI-powered analysis using OpenAI
        analysis_result = generate_ai_cv_analysis(cv_text, target_career)

        user_id = f"user_{int(datetime.now().timestamp())}"

        return jsonify({
            'user_id': user_id,
            'target_career': target_career,
            'analysis': analysis_result,
            'success': True
        })

    except Exception as e:
        logger.error(f"CV analysis failed: {str(e)}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


def generate_ai_cv_analysis(cv_text: str, target_career: str) -> Dict[str, Any]:
    """Generate comprehensive CV analysis using OpenAI"""
    try:
        career_config = CAREER_CONFIGS.get(target_career, CAREER_CONFIGS['fullstack'])

        prompt = f"""
        Analyze this CV for a career transition to {career_config['title']}.

        CV CONTENT:
        {cv_text[:4000]}

        TARGET CAREER: {career_config['title']}
        REQUIRED SKILLS: {', '.join(career_config['skills'])}
        TYPICAL PROGRAMMING LANGUAGES: {', '.join(career_config['languages'])}

        Provide a comprehensive analysis including:

        1. CURRENT SKILLS: Identify existing technical skills, programming languages, and relevant experience
        2. SKILL GAPS: Identify missing skills needed for the target career
        3. LEARNING RECOMMENDATIONS: Specific learning priorities and timeline
        4. CAREER READINESS: Assessment of current readiness level (0-100%)

        Return ONLY valid JSON in this exact structure:
        {{
            "skills_analysis": {{
                "current_skills": [
                    {{
                        "skill": "skill name",
                        "level": "beginner|intermediate|advanced",
                        "confidence": 0-100,
                        "evidence": "evidence from CV"
                    }}
                ],
                "missing_skills": [
                    {{
                        "skill": "skill name", 
                        "importance": "critical|high|medium|low",
                        "reason": "why this skill is important",
                        "learning_time_weeks": 2
                    }}
                ],
                "skill_gap_score": 65,
                "career_readiness": 45
            }},
            "learning_roadmap": {{
                "overview": "brief overview of learning path",
                "total_duration_weeks": 24,
                "readiness_score": 45,
                "weekly_commitment_hours": 15
            }},
            "career_guidance": {{
                "job_market_analysis": "current market analysis",
                "salary_expectations": "realistic salary ranges",
                "portfolio_projects": ["project1", "project2"],
                "interview_preparation": ["topic1", "topic2"]
            }}
        }}

        Be realistic, specific, and actionable. Focus on practical skills that can be learned.
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert career advisor and technical recruiter. Provide accurate, realistic career transition analysis."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=2000
        )

        result_text = response.choices[0].message.content.strip()
        result_text = clean_json_response(result_text)
        analysis_data = json.loads(result_text)

        logger.info("AI CV analysis completed successfully")
        return analysis_data

    except Exception as e:
        logger.error(f"OpenAI CV analysis failed: {str(e)}")
        return generate_fallback_analysis(target_career)


@app.route('/api/ai/generate-roadmap', methods=['POST'])
def generate_roadmap():
    """Generate AI-powered learning roadmap using OpenAI"""
    try:
        data = request.get_json()
        logger.info("Received roadmap generation request")

        career = data.get('career', 'fullstack')
        experience_level = data.get('experience_level', 'beginner')
        user_name = data.get('user_name', 'Student')
        user_skills = data.get('user_skills', [])
        timeframe_weeks = data.get('timeframe_weeks', 24)

        # Generate roadmap using OpenAI
        roadmap_data = generate_ai_roadmap(career, experience_level, user_name, user_skills, timeframe_weeks)

        if not roadmap_data:
            roadmap_data = generate_fallback_roadmap(career, experience_level, user_name)

        logger.info(f"Roadmap generated successfully for {career}")
        return jsonify({
            "success": True,
            **roadmap_data
        })

    except Exception as e:
        logger.error(f"Roadmap generation failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Failed to generate roadmap: {str(e)}"
        }), 500


def generate_ai_roadmap(career: str, experience_level: str, user_name: str, user_skills: List, timeframe_weeks: int) -> \
Dict[str, Any]:
    """Generate learning roadmap using OpenAI"""
    try:
        career_config = CAREER_CONFIGS.get(career, CAREER_CONFIGS['fullstack'])

        skills_text = ", ".join(
            [skill.get('skill', '') for skill in user_skills]) if user_skills else "No specific skills identified"

        prompt = f"""
        Create a comprehensive, practical learning roadmap for {user_name}, a {experience_level} level learner who wants to become a {career_config['title']}.

        CAREER TARGET: {career_config['title']}
        EXPERIENCE LEVEL: {experience_level}
        USER NAME: {user_name}
        EXISTING SKILLS: {skills_text}
        TIMEFRAME: {timeframe_weeks} weeks
        WEEKLY COMMITMENT: 15 hours per week
        REQUIRED TECHNOLOGIES: {', '.join(career_config['skills'])}
        PROGRAMMING LANGUAGES: {', '.join(career_config['languages'])}

        Generate a structured, industry-relevant learning path with:

        1. 4-6 learning phases with clear progression from fundamentals to advanced
        2. Each phase should have 2-3 practical, project-based modules
        3. Each module must include:
           - Specific, actionable learning objectives
           - Technical skills that will be acquired (focus on {career_config['skills']})
           - Real-world applications and mini-projects
           - Duration in weeks (1-4 weeks per module)
           - 2-3 high-quality, FREE learning resources (tutorials, documentation, interactive platforms)
           - Clear, measurable learning outcomes

        4. Include comprehensive career guidance:
           - Current job market analysis for {career_config['title']} roles
           - Realistic salary expectations for different experience levels
           - Specific portfolio project recommendations
           - Technical interview preparation topics

        Focus on practical, hands-on learning. Include coding exercises, real projects, and industry best practices.

        Return ONLY valid JSON in this exact structure:
        {{
            "overview": "Brief description of the learning path",
            "total_duration_weeks": {timeframe_weeks},
            "weekly_commitment_hours": 15,
            "readiness_score": 65,
            "phases": [
                {{
                    "phase_id": "phase_1",
                    "title": "Phase title",
                    "description": "Phase description", 
                    "duration_weeks": 6,
                    "focus_areas": ["Area 1", "Area 2"],
                    "learning_objectives": ["Objective 1", "Objective 2"],
                    "modules": [
                        {{
                            "module_id": "module_1_1",
                            "title": "Module title",
                            "description": "Module description",
                            "duration_weeks": 3,
                            "technical_skills": ["Skill 1", "Skill 2"],
                            "learning_outcomes": ["Outcome 1", "Outcome 2"],
                            "resources": [
                                {{
                                    "title": "Resource title",
                                    "url": "https://real-website.com/path",
                                    "type": "tutorial|course|documentation|project",
                                    "free": true,
                                    "description": "Brief description"
                                }}
                            ]
                        }}
                    ]
                }}
            ],
            "career_guidance": {{
                "job_market_analysis": "Current market analysis",
                "salary_expectations": "Salary ranges",
                "portfolio_projects": ["Project 1", "Project 2", "Project 3"],
                "interview_preparation": ["Topic 1", "Topic 2", "Topic 3"]
            }}
        }}

        Make it practical, industry-relevant, and tailored for a {experience_level} level learner.
        Include real resources from platforms like freeCodeCamp, MDN, official documentation, Coursera, Udemy free courses, and YouTube tutorials.
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert career advisor and learning path designer. Create practical, actionable learning roadmaps for tech careers."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=3000
        )

        result_text = response.choices[0].message.content.strip()
        result_text = clean_json_response(result_text)
        roadmap_data = json.loads(result_text)

        # Add career information
        roadmap_data['career'] = career

        logger.info("AI roadmap generated successfully")
        return roadmap_data

    except Exception as e:
        logger.error(f"OpenAI roadmap generation failed: {str(e)}")
        return None


@app.route('/api/dashboard/insights', methods=['POST'])
def get_dashboard_insights():
    """Generate AI-powered dashboard insights"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        user_profile = data.get('user_profile')
        progress_data = data.get('progress', {})

        insights = generate_ai_insights(user_profile, progress_data)

        return jsonify({
            "success": True,
            "insights": insights
        })

    except Exception as e:
        logger.error(f"Dashboard insights failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


def generate_ai_insights(user_profile: Dict, progress_data: Dict) -> Dict[str, Any]:
    """Generate personalized insights using OpenAI"""
    try:
        career = user_profile.get('career', 'fullstack')
        career_config = CAREER_CONFIGS.get(career, CAREER_CONFIGS['fullstack'])

        prompt = f"""
        Generate personalized learning insights and recommendations for a user pursuing a career as a {career_config['title']}.

        USER PROFILE:
        - Career Target: {career_config['title']}
        - Experience Level: {user_profile.get('experience', 'beginner')}
        - Current Progress: {progress_data}

        Provide:
        1. PROGRESS_ANALYSIS: Analysis of current learning progress and strengths
        2. RECOMMENDATIONS: Specific recommendations for next learning steps
        3. MOTIVATION: Encouraging insights and motivation
        4. SKILL_FOCUS: Key skills to focus on next

        Return ONLY valid JSON:
        {{
            "progress_analysis": "analysis of current progress",
            "recommendations": [
                "recommendation 1",
                "recommendation 2", 
                "recommendation 3"
            ],
            "motivation": "encouraging message",
            "skill_focus": ["skill1", "skill2", "skill3"],
            "next_steps": ["step1", "step2"]
        }}
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are an encouraging learning coach. Provide personalized, actionable insights."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=1500
        )

        result_text = response.choices[0].message.content.strip()
        result_text = clean_json_response(result_text)
        insights = json.loads(result_text)

        return insights

    except Exception as e:
        logger.error(f"OpenAI insights generation failed: {str(e)}")
        return generate_fallback_insights(user_profile)


@app.route('/api/jobs/match', methods=['POST'])
def find_matching_jobs():
    """AI-powered job matching"""
    try:
        data = request.get_json()
        skills = data.get('skills', [])
        career = data.get('career', '')
        experience = data.get('experience', 'beginner')

        matched_jobs = generate_ai_job_matches(skills, career, experience)

        return jsonify({
            "matched_jobs": matched_jobs
        })

    except Exception as e:
        logger.error(f"Job matching failed: {str(e)}")
        return jsonify({"matched_jobs": []})


def generate_ai_job_matches(skills: List, career: str, experience: str) -> List[Dict]:
    """Generate realistic job matches using OpenAI"""
    try:
        career_config = CAREER_CONFIGS.get(career, CAREER_CONFIGS['fullstack'])
        skills_text = ", ".join([skill.get('skill', '') for skill in skills]) if skills else "Basic programming skills"

        prompt = f"""
        Generate 5-6 realistic job matches for a {experience} level {career_config['title']} with these skills: {skills_text}

        For each job, provide:
        - Realistic job title and company
        - Location (mix of remote and major tech cities)
        - Match percentage based on skills
        - Matching skills and missing skills
        - Realistic salary range
        - Brief job description

        Return ONLY valid JSON with "matched_jobs" array:
        {{
            "matched_jobs": [
                {{
                    "id": "job_1",
                    "title": "Job Title",
                    "company": "Company Name",
                    "location": "City, State or Remote",
                    "match_percentage": 75,
                    "matching_skills": ["skill1", "skill2"],
                    "missing_skills": ["skill3", "skill4"],
                    "salary_range": "$XX,XXX - $XXX,XXX",
                    "job_description": "Brief description",
                    "application_url": "#",
                    "tags": ["tag1", "tag2"]
                }}
            ]
        }}

        Make it realistic for the current job market.
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a technical recruiter. Generate realistic job matches based on skills and experience."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )

        result_text = response.choices[0].message.content.strip()
        result_text = clean_json_response(result_text)
        jobs_data = json.loads(result_text)

        return jobs_data.get('matched_jobs', [])

    except Exception as e:
        logger.error(f"OpenAI job matching failed: {str(e)}")
        return generate_fallback_jobs(career, experience)


@app.route('/api/learning/generate-lesson', methods=['POST'])
def generate_lesson():
    """Generate AI-powered learning content"""
    try:
        data = request.get_json()
        topic = data.get('topic', 'Programming Basics')
        difficulty = data.get('difficulty', 'beginner')
        language = data.get('language', 'JavaScript')

        lesson_content = generate_ai_lesson(topic, difficulty, language)

        return jsonify({
            "success": True,
            "lesson": lesson_content
        })

    except Exception as e:
        logger.error(f"Lesson generation failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


def generate_ai_lesson(topic: str, difficulty: str, language: str) -> Dict[str, Any]:
    """Generate learning lesson using OpenAI"""
    try:
        prompt = f"""
        Create a comprehensive learning lesson about: {topic}
        Programming Language: {language}
        Difficulty Level: {difficulty}

        Include:
        - Clear learning objectives
        - Detailed theory content with examples
        - Code examples in {language}
        - Common mistakes and how to avoid them
        - Practice exercises
        - Real-world applications

        Return structured JSON content.
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert programming instructor. Create engaging, educational content."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=2500
        )

        result_text = response.choices[0].message.content.strip()
        result_text = clean_json_response(result_text)
        lesson_data = json.loads(result_text)

        return lesson_data

    except Exception as e:
        logger.error(f"OpenAI lesson generation failed: {str(e)}")
        return generate_fallback_lesson(topic, language)


# Helper functions
def extract_text_from_file(file) -> str:
    """Extract text from uploaded file"""
    text = ""
    filename = file.filename.lower()

    try:
        file.seek(0)

        if filename.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages[:5]:  # Limit to first 5 pages
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        elif filename.endswith('.docx'):
            doc = docx.Document(file)
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text += paragraph.text + "\n"

        elif filename.endswith('.txt'):
            text = file.read().decode('utf-8', errors='ignore')

    except Exception as e:
        logger.error(f"File extraction error: {str(e)}")
        text = "Sample CV content for AI analysis: Programming experience, project work, technical skills."

    return text.strip()


def clean_json_response(text: str) -> str:
    """Clean JSON response from OpenAI"""
    # Remove markdown code blocks
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'\s*```', '', text)
    text = text.strip()

    # Find the first { and last }
    start = text.find('{')
    end = text.rfind('}') + 1
    if start != -1 and end != 0:
        text = text[start:end]

    return text


def get_salary_range(career: str) -> str:
    """Get realistic salary range for career"""
    salary_ranges = {
        'fullstack': '$70,000 - $130,000',
        'frontend': '$60,000 - $120,000',
        'backend': '$75,000 - $140,000',
        'datascience': '$80,000 - $150,000',
        'machinelearning': '$90,000 - $160,000',
        'mobile': '$65,000 - $130,000',
        'devops': '$85,000 - $150,000'
    }
    return salary_ranges.get(career, '$70,000 - $120,000')


def get_growth_outlook(career: str) -> str:
    """Get growth outlook for career"""
    outlooks = {
        'fullstack': 'High Demand',
        'frontend': 'High Demand',
        'backend': 'High Demand',
        'datascience': 'Very High Demand',
        'machinelearning': 'Very High Demand',
        'mobile': 'High Demand',
        'devops': 'High Demand'
    }
    return outlooks.get(career, 'High Demand')


# Fallback generators
def generate_fallback_analysis(target_career: str) -> Dict[str, Any]:
    """Generate fallback analysis when AI fails"""
    career_config = CAREER_CONFIGS.get(target_career, CAREER_CONFIGS['fullstack'])

    return {
        "skills_analysis": {
            "current_skills": [
                {"skill": "CV Analysis", "level": "beginner", "confidence": 50, "evidence": "Uploaded CV"}
            ],
            "missing_skills": [
                {"skill": f"{career_config['title']} Fundamentals", "importance": "critical",
                 "reason": "Core requirements", "learning_time_weeks": 4},
                {"skill": "Project Development", "importance": "high", "reason": "Practical experience needed",
                 "learning_time_weeks": 6}
            ],
            "skill_gap_score": 70,
            "career_readiness": 30
        },
        "learning_roadmap": {
            "total_duration_weeks": 24,
            "readiness_score": 30,
            "weekly_commitment_hours": 15,
            "overview": f"Learning path for {career_config['title']}"
        },
        "career_guidance": {
            "job_market_analysis": "Strong demand for tech roles with competitive salaries",
            "salary_expectations": get_salary_range(target_career),
            "portfolio_projects": ["Build a portfolio project", "Contribute to open source"],
            "interview_preparation": ["Technical interviews", "System design", "Behavioral questions"]
        }
    }


def generate_fallback_roadmap(career: str, experience_level: str, user_name: str) -> Dict[str, Any]:
    """Generate fallback roadmap when AI fails"""
    career_config = CAREER_CONFIGS.get(career, CAREER_CONFIGS['fullstack'])

    return {
        "overview": f"Comprehensive {career_config['title']} learning path for {user_name}",
        "total_duration_weeks": 24,
        "weekly_commitment_hours": 15,
        "readiness_score": 50,
        "career": career,
        "phases": [
            {
                "phase_id": "phase_1",
                "title": f"{career_config['title']} Fundamentals",
                "description": f"Build foundation in {career_config['title'].lower()} concepts and technologies",
                "duration_weeks": 6,
                "focus_areas": ["Core Concepts", "Essential Tools"],
                "learning_objectives": ["Master fundamental concepts", "Learn essential development tools"],
                "modules": [
                    {
                        "module_id": "module_1_1",
                        "title": f"{career_config['languages'][0]} Programming",
                        "description": f"Learn {career_config['languages'][0]} programming fundamentals",
                        "duration_weeks": 3,
                        "technical_skills": [career_config['languages'][0], "Programming Basics"],
                        "learning_outcomes": [f"Write basic {career_config['languages'][0]} programs",
                                              "Understand programming concepts"],
                        "resources": [
                            {
                                "title": f"{career_config['languages'][0]} Documentation",
                                "url": "https://developer.mozilla.org/",
                                "type": "documentation",
                                "free": True,
                                "description": f"Official {career_config['languages'][0]} documentation"
                            }
                        ]
                    }
                ]
            }
        ],
        "career_guidance": {
            "job_market_analysis": f"Strong demand for {career_config['title']} roles",
            "salary_expectations": get_salary_range(career),
            "portfolio_projects": ["Build a complete project", "Create portfolio showcase"],
            "interview_preparation": ["Technical skills", "System design", "Behavioral questions"]
        }
    }


def generate_fallback_insights(user_profile: Dict) -> Dict[str, Any]:
    """Generate fallback insights"""
    return {
        "progress_analysis": "Continue your learning journey with consistent practice",
        "recommendations": ["Focus on practical projects", "Build a portfolio", "Practice regularly"],
        "motivation": "Keep going! Every step brings you closer to your career goals.",
        "skill_focus": ["Core programming", "Project development", "Problem solving"],
        "next_steps": ["Complete current modules", "Start a new project", "Review fundamentals"]
    }


def generate_fallback_jobs(career: str, experience: str) -> List[Dict]:
    """Generate fallback job matches"""
    career_config = CAREER_CONFIGS.get(career, CAREER_CONFIGS['fullstack'])

    return [
        {
            "id": "job_1",
            "title": f"{experience.title()} {career_config['title']}",
            "company": "Tech Company Inc.",
            "location": "Remote",
            "match_percentage": 65,
            "matching_skills": ["Programming", "Problem Solving"],
            "missing_skills": ["Advanced Frameworks", "System Design"],
            "salary_range": get_salary_range(career),
            "job_description": f"Great opportunity for {experience} level {career_config['title'].lower()}",
            "application_url": "#",
            "tags": [career, experience, "remote"]
        }
    ]


def generate_fallback_lesson(topic: str, language: str) -> Dict[str, Any]:
    """Generate fallback lesson content"""
    return {
        "title": f"{topic} in {language}",
        "objectives": [f"Understand {topic} concepts", f"Implement {topic} in {language}"],
        "content": f"Learn {topic} using {language} programming language.",
        "examples": [f"// {language} example for {topic}"],
        "exercises": [f"Practice implementing {topic} in {language}"]
    }


if __name__ == '__main__':
    print("🚀 COMPLETE AI-POWERED Career Platform Started")
    print("✅ All endpoints ready with OpenAI integration:")
    print("   - /api/health")
    print("   - /api/careers/list")
    print("   - /api/skills/analyze (OpenAI CV Analysis)")
    print("   - /api/ai/generate-roadmap (OpenAI Roadmap Generation)")
    print("   - /api/dashboard/insights (OpenAI Insights)")
    print("   - /api/jobs/match (OpenAI Job Matching)")
    print("   - /api/learning/generate-lesson (OpenAI Lesson Generation)")
    app.run(debug=True, port=5000, threaded=True)