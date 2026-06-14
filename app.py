import streamlit as st
import google.generativeai as genai
import tempfile
import os

# ==========================================
# 1. 기본 설정 및 API 키 불러오기
# ==========================================
st.set_page_config(page_title="해그미: AI 해금 튜터", page_icon="🎵", layout="wide")

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("앗! API 키 설정이 빠져있습니다. Streamlit Secrets 설정을 확인해주세요.")
    st.stop()

# 최신 모델명 설정 (AI 스튜디오에서 확인하신 명칭으로 수정 가능)
MODEL_NAME = 'gemini-3.1-pro-preview' 

# ==========================================
# 2. 공통 함수
# ==========================================
def get_ai_feedback(system_prompt, audio_file_bytes, file_extension, user_message, reference_files=None):
    model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=system_prompt)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp_file:
        tmp_file.write(audio_file_bytes)
        tmp_file_path = tmp_file.name
        
    student_audio = genai.upload_file(path=tmp_file_path)
    
    contents = []
    if reference_files:
        contents.append("다음은 기준 음원들입니다. 이 소리들의 파형과 주파수를 평가 기준으로 삼아주세요.")
        for ref_file in reference_files:
            if os.path.exists(ref_file):
                uploaded_ref = genai.upload_file(path=ref_file)
                contents.append(uploaded_ref)
                
    contents.append("다음은 학생의 연주 음원입니다.")
    contents.append(student_audio)
    contents.append(user_message)
    
    response = model.generate_content(contents)
    os.remove(tmp_file_path)
    return response.text

# ==========================================
# 3. 각 단계별 설정
# ==========================================
st.sidebar.title("🎵 해금 학습 메뉴")
module_stage = st.sidebar.radio("진행할 단계:", ["1단계: 조율사 해그미 (준비)", "2단계: 시김새 해그미 (기초)", "3단계: 진도아리랑 해그미 (실전)", "4단계: 성찰 해그미 (마무리)"])

# 1단계
if module_stage == "1단계: 조율사 해그미 (준비)":
    st.title("🎵 1단계: 조율사 해그미")
    st.write("### 🎧 선생님의 기준 음원 들어보기")
    with st.expander("시범 연주 확인하기"):
        st.audio("Yukja_reference_Mi.m4a"); st.audio("Yukja_reference_La.m4a"); st.audio("Yukja_reference_Do.m4a")
    
    audio_record = st.audio_input("내 연주 녹음하기")
    if audio_record and st.button("피드백 받기"):
        res = get_ai_feedback("너는 친절한 해금 조율사야...", audio_record.getvalue(), "wav", "피드백해줘", ["Yukja_reference_Mi.m4a", "Yukja_reference_La.m4a", "Yukja_reference_Do.m4a"])
        st.write(res)

# 2단계
elif module_stage == "2단계: 시김새 해그미 (기초)":
    st.title("🎵 2단계: 시김새 해그미")
    st.write("### 🎧 시김새 기준 음원 들어보기")
    with st.expander("시범 연주 확인하기"):
        st.audio("Yukja_sigimsae_Mi.m4a"); st.audio("Yukja_sigimsae_La.m4a"); st.audio("Yukja_sigimsae_Dosi.m4a")
    
    audio_record = st.audio_input("시김새 연주 녹음하기")
    if audio_record and st.button("피드백 받기"):
        res = get_ai_feedback("너는 육자배기토리 전문 해금 튜터야...", audio_record.getvalue(), "wav", "시김새 분석해줘", ["Yukja_sigimsae_Mi.m4a", "Yukja_sigimsae_La.m4a", "Yukja_sigimsae_Dosi.m4a"])
        st.write(res)

# 3단계
elif module_stage == "3단계: 진도아리랑 해그미 (실전)":
    st.title("🎵 3단계: 진도아리랑 해그미")
    st.write("### 🎧 진도아리랑 모범 연주 들어보기")
    with st.expander("시범 연주 확인하기"):
        st.audio("Jindo1-1.m4a"); st.audio("Jindo2-1.m4a")
    
    audio_record = st.audio_input("진도아리랑 연주 녹음하기")
    if audio_record and st.button("피드백 받기"):
        res = get_ai_feedback("너는 진도아리랑 전문 해금 튜터야...", audio_record.getvalue(), "wav", "전체 연주 분석해줘", ["Jindo1-1.m4a", "Jindo2-1.m4a"])
        st.write(res)

# 4단계
elif module_stage == "4단계: 성찰 해그미 (마무리)":
    st.title("🏆 4단계: 성찰 해그미")
    user_reflection = st.text_area("오늘 연습 소감을 적어주세요.")
    if user_reflection and st.button("마음 지도 받기"):
        model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction="너는 학생의 성찰을 돕는 튜터야.")
        st.write(model.generate_content(str(user_reflection)).text)
