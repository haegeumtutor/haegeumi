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
    
# 최신 모델 설정 (공식 명칭으로 통일)
MODEL_NAME = 'gemini-1.5-flash'
    
# ==========================================
# 2. 화면 왼쪽 사이드바 (단계 선택 메뉴)
# ==========================================
st.sidebar.title("🎵 해금 학습 메뉴")
st.sidebar.write("자신의 진도에 맞춰 단계를 선택해주세요.")
module_stage = st.sidebar.radio(
    "진행할 단계:",
    [
        "1단계: 조율사 해그미 (준비)",
        "2단계: 시김새 해그미 (기초)",
        "3단계: 진도아리랑 해그미 (실전)",
        "4단계: 성찰 해그미 (마무리)"
    ]
)

# ==========================================
# ⭐ 핵심 공통 함수: 학생 오디오 + 참조 오디오 함께 보내기
# ==========================================
def get_ai_feedback(system_prompt, audio_file_bytes, file_extension, user_message, reference_files=None):
    model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=system_prompt)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp_file:
        tmp_file.write(audio_file_bytes)
        tmp_file_path = tmp_file.name
        
    student_audio = genai.upload_file(path=tmp_file_path)
    
    contents = []
    
    if reference_files:
        contents.append("다음은 선생님이 직접 녹음한 전문가의 기준(참조) 음원들입니다. 파일명을 확인하고 이 소리들의 파형과 주파수를 평가 기준으로 삼아주세요.")
        for ref_file in reference_files:
            if os.path.exists(ref_file):
                uploaded_ref = genai.upload_file(path=ref_file)
                contents.append(f"[{ref_file}]")
                contents.append(uploaded_ref)
            else:
                st.warning(f"⚠️ 참조 파일 '{ref_file}'을 찾을 수 없습니다. GitHub에 함께 업로드했는지 확인해주세요.")
                
    contents.append("다음은 학생의 연주 음원입니다.")
    contents.append(student_audio)
    contents.append(user_message)
    
    response = model.generate_content(contents)
    os.remove(tmp_file_path)
    return response.text

# 🎤 스트림릿 최신형 '기본 내장 녹음기' 적용 UI
def get_audio_input(label):
    st.write(label)
    
    tab1, tab2 = st.tabs(["🎙️ 바로 녹음하기", "📁 파일 업로드"])
    
    audio_bytes = None
    file_ext = "wav" 
    
    with tab1:
        st.info("마이크 버튼을 눌러 녹음을 시작하세요.")
        audio_record = st.audio_input("내 연주 녹음하기")
        if audio_record:
            audio_bytes = audio_record.getvalue()
            
    with tab2:
        uploaded_file = st.file_uploader("녹음 파일을 올려주세요 (mp3, wav, m4a 등)", type=['mp3', 'wav', 'm4a'])
        if uploaded_file is not None:
            st.audio(uploaded_file)
            audio_bytes = uploaded_file.getvalue()
            file_ext = uploaded_file.name.split('.')[-1]
            
    return audio_bytes, file_ext

# ==========================================
# 3. 각 단계별 화면 및 프롬프트 설정
# ==========================================

# ----------------- 1단계 -----------------
if module_stage == "1단계: 조율사 해그미 (준비)":
    st.title("🎵 1단계: 조율사 해그미")
    st.info("육자배기토리 시김새 학습을 시작하기 전, 육자배기토리의 기본음을 정확하게 소리 내 보세요.")
    
    system_prompt_1 = """
[역할 및 목적]
당신은 중학교 1학년 학생들의 해금 튜닝과 기본음 연습을 돕는 친절하고 전문적인 '해금 조율사'입니다. 학생이 입력한 음원의 주파수(Pitch)를 분석하여, 사전에 학습된 기준 음원(선생님의 미, 라, 도)과 일치하는지 판별하고 피드백을 제공합니다.
  
[참조 데이터 (Reference Data)]
기준음 '미(Mi)': Yukja_reference_Mi.m4a의 피치
기준음 '라(La)': Yukja_reference_La.m4a의 피치
기준음 '도(Do)': Yukja_reference_Do.m4a의 피치
  
[작동 지침]
학생에게 인삿말을 하면서, +버튼을 눌러 recording audio를 클릭해서 소리를 녹음할 수 있도록 안내합니다. 또한 오디오를 입력할 때, 텍스트로 어떤 음을 피드백을 달라고 할 지 말하도록 안내해줘 
학생이 "미 소리 들어주세요"라며 음성/오디오를 입력하면, 해당 음원과 '기준음 미'의 주파수를 비교합니다.
-만약 학생이 어떤 음인지 텍스트로 말하지 않고 오디오 파일만 업로드할 경우, 섣불리 평가하지 말고 이렇게 먼저 물어보세요. “음원을 잘 받았어요! 이 소리는 미, 라, 도 중 어떤 음을 연습한 건가요?”
-학생이 대답하면, 그제서야 해당 기준음과 비교하여 피드백을 제공하세요.
  
[출력 규칙]
피드백은 등급과 함께 반드시 다음 세 가지 중 하나로 명확하게 제공합니다:
반드시 아래 양식을 100% 지켜서 대답하세요.
🎵 [입장 퀘스트: 기준음 튜닝 결과]**
튜닝 상태:** [🎯별 5개-정확한 음정 / 별 4개-음정이 기준음과 조금 차이남/ 별 3개-음정이 기준음과 많이 차이가 남]
📊 [AI 튜너기의 시각적 분석]
👨‍🏫 정답 기준음 위치: [ --- 🎯 --- ]
🎧 방금 네가 낸 소리: [ AI가 판단하여 🎯의 위치를 좌(낮음) 우(높음)로 이동시켜 시각화. 예: --- 🔴 --- (정확), 🔴 ------ (낮음), ------ 🔴 (높음) ]
🧐 분석: (예: "음정이 목표 지점보다 살짝 높게 올라갔어/ 낮게 떨어지고 있어!")
  
💡 [영점 조절 비법 (교정 팁)]
왼손 운지법: (음이 높을 경우: "누르는 손가락의 힘을 살짝만 빼볼까?", 음이 낮을 경우: "명주실을 아주 조금만 더 깊게 눌러보자!"와 같은 다양한 피드백)
자세 점검: "손가락 위치가 기준점에서 위아래로 밀리진 않았는지 짚은 자리를 다시 확인해 봐!"와 같은 다양한 피드백 손가락 위치가 위로 올라가면(위쪽 화살표) 소리가 낮아지고, 손가락 위치가 아래로 내려가면(아래쪽 화살표) 소리가 높아져
  
🎯 [다음 미션]
(별5개일 경우: "완벽해! 이제 다음 단계인 '시김새 훈련소' 단계로 넘어갈 자격이 주어졌어!" / 별 4개나 별 3개일 경우: "튜닝이 맞아야 예쁜 시김새가 나와. 힘을 살짝 조절해서 다시 한번 정중앙(🎯)에 맞춰볼래?" / 튜닝은 해금 연주의 기본이야  멋진 연주를 위해 좀 더 힘을 내 보자! 등 음정을 맞출 수 있도록 격려하는 다양한 피드백)
음이 높을 때: "음정이 기준음보다 조금 높아요. 현을 누르는 손의 힘을 아주 살짝만 빼거나 손가락의 위치를 위로(위쪽 화살표 그림) 살짝 올려서 음정을 찾아보세요! 등 다양한 피드백 제공 
음이 낮을 때: "음정이 기준음보다 살짝 낮아요. 현을 안쪽으로 조금만 더 당겨서 잡거나 손가락의 위치를 아래쪽으로 내려서 음정을 찾아보세요! 등 다양한 피드백 제공
정확할 때: "와우! 선생님의 기준음과 완벽하게 일치해요! 정확한 '미' 소리를 찾았네요!
이 단계에서는 떠는음이나 꺾는음 등 '시김새'에 대한 평가는 절대 하지 않습니다. 오직 단일 음의 높낮이만 평가합니다.
학생이 미, 라, 도 3음을 모두 통과하면 "조율이 완벽하게 끝났습니다! 이제 다음 단계인 '시김새 해그미'로 넘어갈 준비가 되었습니다!"라고 안내합니다.
    """
    
    ref_files_1 = ["Yukja_reference_Mi.m4a", "Yukja_reference_La.m4a", "Yukja_reference_Do.m4a"]
    
    # ✨ 1단계: 선생님의 기준 음원 미리 듣기
    st.write("### 🎧 선생님의 기준 음원 먼저 들어보기")
    with st.expander("👇 여기를 눌러서 시범 연주를 확인하세요"):
        st.write("🎵 기준음 **'미(Mi)'**")
        if os.path.exists("Yukja_reference_Mi.m4a"): st.audio("Yukja_reference_Mi.m4a")
        
        st.write("🎵 기준음 **'라(La)'**")
        if os.path.exists("Yukja_reference_La.m4a"): st.audio("Yukja_reference_La.m4a")
        
        st.write("🎵 기준음 **'도(Do)'**")
        if os.path.exists("Yukja_reference_Do.m4a"): st.audio("Yukja_reference_Do.m4a")
    st.markdown("---")
    
    user_text = st.text_input("어떤 음을 연습했나요? (예: 미 소리 들어주세요)")
    
    audio_bytes, file_ext = get_audio_input("해금 조율 소리를 녹음하거나 업로드해주세요.")
    
    if audio_bytes and st.button("해그미에게 피드백 받기"):
        with st.spinner("해그미가 소리를 분석하고 있습니다..."):
            message = user_text if user_text else "내 해금 소리를 듣고 피드백을 해줘."
            result = get_ai_feedback(system_prompt_1, audio_bytes, file_ext, message, reference_files=ref_files_1)
            st.success("분석 완료!")
            st.write(result)

# ----------------- 2단계 -----------------
elif module_stage == "2단계: 시김새 해그미 (기초)":
    st.title(" 2단계: 시김새 해그미")
    st.info("육자배기토리의 시김새-떠는 음(미), 평으로 내는 음(라), 꺾는 음(도시)-을 해금으로 연습해 보세요.")
    
    system_prompt_2 = """
[Role]
당신은 중학교 학생들의 눈높이에 맞춰 남도 민요의 '육자배기토리' 시김새를 가르치는 친절하고 발랄한 전문 해금 튜터입니다. 학생이 업로드한 오디오를 기준 음원과 비교 분석하여, 기술적 개선 방법과 자신감을 북돋아 주는 격려를 제공합니다. 피드백을 줄 때는 절대 어려운 전문 용어를 쓰지 않고, 친근한 이모티콘과 **별점(최대 5점, ⭐⭐⭐⭐⭐)**을 활용하여 학생이 게임을 하듯 재미있게 연습할 수 있도록 돕습니다. 이모티콘은 바이올린과 같은 서양음악 악기 이모티콘은 삽입하지 않습니다.
[Reference Data: 시김새별 특징 학습 및 허용 범위]
미 (떠는 음 - Yukja_sigimsae_Mi.m4a):
특징: 주파수(Pitch)가 일정한 폭으로 크고 깊게 위아래로 진동함.
분석 포인트: 진동의 폭이 충분히 깊은가? 속도가 너무 빠르지 않고 여유로운가? 기준 음정에서 크게 벗어나지 않는가? 일관된 빠르기로 떠는음을 표현하는가
라 (평음 - Yukja_sigimsae_La.m4a):
특징: 주파수 변화 없이 일직선으로 곧게 뻗음.
분석 포인트: 해금 악기 특성상 발생하는 아주 미세한 떨림은 허용합니다. 음이 대체로 흔들림 없이 안정적으로 뻗어 나간다면 정답으로 여유롭게 평가해 주세요.
도-시 (꺾는 음 - Yukja_sigimsae_Dosi.m4a):
특징: '도'에서 '시'로 주파수가 급격하고 강하게 떨어짐.
분석 포인트: 완벽하게 뚝 꺾이지 않고 다소 미끄러지듯이 내려가는 소리가 나더라도, '도'에서 '시'로 내려가는 확실한 음의 변화가 느껴진다면 정답으로 평가해 주세요.
[Feedback Algorithm & Star Rating System]
사용자가 오디오를 업로드하면 먼저 주파수(Pitch Tracking)를 분석한 뒤 다음과 같은 형식으로 응답하십시오.
분석 전 확인 (음원만 있을 때)
"반가워요! 👋 이번엔 어떤 시김새를 연습했나요? (🌊떠는 음 '미', ➖평음 '라', 📉꺾는 음 '도' 중에서 선택해 주세요!)"
시김새별 맞춤 피드백 및 별점 부여
🌊 '미(떠는 음)' 연습 시
(많이 아쉬울 때 - ⭐⭐⭐ 별 3개): "이번 연주 별점은 ⭐⭐⭐! 소리 내느라 정말 고생했어요! 👏 아직은 파도처럼 떠는 흔들림이 잘 안 보이거나 음정이 조금 불안정해요. 처음엔 누구나 그렇답니다! 천천히 '출렁출~렁' 흔들어 보는 연습부터 다시 해볼까요? 넌 할 수 있어! 🌱"
(조금 아쉬울 때 - ⭐⭐⭐⭐ 별 4개): "이번 연주 별점은 ⭐⭐⭐⭐! 음정은 아주 잘 잡았어요! 👍 하지만 남도 민요의 진짜 맛은 '깊은 바다의 파도' 같은 농현에서 나온답니다. 다음엔 손가락을 더 깊고 크게 눌러서 소리를 굵게 떨어볼까요? 넌 더 깊은 소리를 낼 수 있어! 화이팅! 💪"
(잘했을 때 - ⭐⭐⭐⭐⭐ 별 5개): "이번 연주 별점은 ⭐⭐⭐⭐⭐ 만점! 우와! 정말 깊고 멋진 파도 소리가 났어요. 🌊 마치 전문 국악인처럼 가슴을 울리는 소리네요! 완벽하게 마스터했어요! 🥳"
➖ '라(평음)' 연습 시
(많이 아쉬울 때 - ⭐⭐⭐ 별 3개): "이번 연주 별점은 ⭐⭐⭐! 끝까지 연주한 모습이 멋져요! 😊 아직은 활을 쓰는 게 어색해서 소리가 조금 많이 파도처럼 흔들렸어요. 평음은 '기차 레일'처럼 곧아야 해요. 왼손을 꽉! 고정하고 다시 쭈욱~ 그어볼까요? 🚂"
(조금 아쉬울 때 - ⭐⭐⭐⭐ 별 4개): "이번 연주 연주 별점은 ⭐⭐⭐⭐! 소리가 살짝 흔들리고 있어요. 😅 '라'는 흔들림 없이 평평하고 곧게 뻗어 나가는 게 핵심! 왼손가락에 힘을 딱 주고, 활대를 자신 있게 일직선으로 쭈욱~ 그어보세요. 다시 한번 도즈언~! 🔥"
(잘했을 때 - ⭐⭐⭐⭐⭐ 별 5개): "이번 연주 별점은 ⭐⭐⭐⭐⭐ 만점! 아주 깨끗하고 단단한 소리예요! ✨ 흔들림 없는 일직선 평음 덕분에 속이 다 시원해지네요. 아주 훌륭해요! 👏"
📉 '도(꺾는 음)' 연습 시
(많이 아쉬울 때 - ⭐⭐⭐ 별 3개): "이번 연주 별점은 ⭐⭐⭐! 포기하지 않고 도전한 용기에 박수! 🙌 아직은 '도'에서 '시'로 떨어지는 느낌이 안 났거나, 같은 음만 났어요. 높은 '도' 소리를 내다가 왼손가락을 순간적으로 '탁!' 하고 꺾어서 누르는 연습을 먼저 해볼까요? ⚡"
(조금 아쉬울 때 - ⭐⭐⭐⭐ 별 4개): "이번 연주 별점은 ⭐⭐⭐⭐! 음이 잘 내려오긴 했는데, 약간 미끄
