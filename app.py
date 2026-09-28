import io
import json
import tarfile
import zipfile
import streamlit as st
from google import genai
from PIL import Image

# 페이지 기본 설정
st.set_page_config(
    page_title="🤖 엔트리 AI 학습 도우미",
    page_icon="🤖",
    layout="centered"
)

# 엔트리 .ent 파일 분석 함수
def extract_entry_json(file_bytes: bytes) -> dict:
    try:
        with tarfile.open(fileobj=io.BytesIO(file_bytes), mode="r:*") as tar:
            for member in tar.getmembers():
                if member.name.replace("\\", "/").endswith("project.json"):
                    f = tar.extractfile(member)
                    if f:
                        return json.load(f)
    except Exception:
        pass

    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes), "r") as z:
            for name in z.namelist():
                if name.replace("\\", "/").endswith("project.json"):
                    with z.open(name) as f:
                        return json.load(f)
    except Exception:
        pass
    return None

st.title("🤖 엔트리 AI 학습 도우미")
st.write("중학교 1학년 정보 수업 전담 AI 선생님입니다.")

# 1. 파일/캡처 이미지 업로드 영역
st.subheader("1. 캡처 이미지 또는 파일(.ent) 등록")

uploaded_file = st.file_uploader(
    "💡 캡처한 이미지(Ctrl+V 붙여넣기 가능) 또는 엔트리 파일(.ent)을 등록하세요",
    type=["png", "jpg", "jpeg", "webp", "ent"],
    help="컴퓨터 화면 캡처(Win+Shift+S 등) 후 이미지 파일 업로드나 클릭 후 Ctrl+V로 첨부할 수 있습니다."
)

# 등록된 이미지 미리보기 출력
if uploaded_file is not None:
    filename = uploaded_file.name.lower()
    if uploaded_file.type.startswith("image/") or any(filename.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]):
        st.success("✅ 이미지가 정상적으로 등록되었습니다!")
        # use_container_width=True 로 수정하여 TypeError 해결
        st.image(uploaded_file, caption="📷 등록된 엔트리 화면 미리보기", use_container_width=True)
    elif filename.endswith(".ent"):
        st.success(f"✅ 엔트리 프로젝트 파일 등록 완료: {uploaded_file.name}")

# 2. 질문 입력 영역
st.subheader("2. 고민이나 질문 입력")
student_question = st.text_area(
    "질문 내용",
    placeholder="예: 파랑에 닿으면 오른쪽으로 회전하고 싶은데 방법을 알려줘."
)

# 제출 버튼
if st.button("💡 AI 선생님에게 힌트 요청하기", type="primary"):
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("API 키가 설정되지 않았습니다. Streamlit Secrets 설정을 확인해 주세요.")
        st.stop()

    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)

    if not uploaded_file:
        st.warning("엔트리 화면 캡처 이미지나 파일(.ent)을 등록해 주세요!")
        st.stop()

    if not student_question.strip():
        st.warning("질문을 입력해 주세요!")
        st.stop()

    # 중1 정보 교과 가드레일 프롬프트
    system_prompt = f"""
너는 대한민국 중학교 1학년 학생들을 위한 친절하고 따뜻한 '정보(컴퓨터) 교과 전담 AI 선생님'이야.

[학생의 질문]
"{student_question}"

[핵심 역할 및 범위 제한 - 매우 중요!]
1. 너는 오직 **중학교 1학년 정보 교과 과정**과 관련된 질문에만 답변해야 해.
   - 허용 범위: 엔트리(Entry) 블록코딩, 알고리즘(순차/선택/반복), 변수, 리스트, 컴퓨터 구조, 정보 윤리, 저작권, 개인정보 보호, 2진수와 디지털 표현 등.
2. 학생의 질문이나 이미지 내용이 중1 정보 교과와 **관련 없는 내용**(예: 타 과목 숙제, 연예인/게임 이야기, 일상 잡담, 장난스러운 질문 등)이라면 절대 그 질문에 답해주지 마.
   - 관외 질문 처리 예시: "저는 중학교 정보 교과와 엔트리 코딩을 도와주는 AI 선생님이에요! 💻 정보 수업 내용이나 코딩에 대해 궁금한 점을 질문해 주세요. 😊"라는 메시지 하나만 친절하게 남기고 힌트는 제공하지 마세요.

[답변 지침 (정보 교과 관련 질문일 경우만 적용)]
1. 절대 정답 코드를 직접 완성해주거나 답을 바로 알려주지 마세요.
2. 학생이 스스로 원인을 깨달을 수 있도록 문제점을 짚어주는 2~3단계 소크라테스식 힌트를 제시하세요.
3. 엔트리 블록 이름(예: '~색에 닿았는가?', 'n번 반복하기' 등)을 구체적으로 언급하세요.
4. 중학교 1학년 수준에 맞는 다정하고 격려하는 말투를 사용하세요.
"""

    with st.spinner("🤖 AI 선생님이 코드를 분석하고 힌트를 작성 중입니다..."):
        try:
            file_bytes = uploaded_file.getvalue()
            filename = uploaded_file.name.lower()
            prompt_contents = []

            if uploaded_file.type.startswith("image/") or any(filename.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]):
                image = Image.open(io.BytesIO(file_bytes))
                prompt_contents = [image, system_prompt + "\n\n[첨부 자료]: 학생이 제출한 캡처 이미지입니다."]
            elif filename.endswith(".ent"):
                entry_data = extract_entry_json(file_bytes)
                if not entry_data:
                    st.error(".ent 파일 분석에 실패했습니다.")
                    st.stop()
                json_str = json.dumps(entry_data, ensure_ascii=False, indent=2)
                prompt_contents = [system_prompt + f"\n\n[학생의 엔트리 프로젝트 JSON]\n{json_str[:4000]}"]

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt_contents
            )

            st.success("📢 AI 선생님의 힌트")
            st.write(response.text)

        except Exception as e:
            st.error(f"오류가 발생했습니다: {str(e)}")
