from __future__ import annotations

from datetime import date, datetime, timedelta
from io import StringIO
from pathlib import Path

import pandas as pd
import streamlit as st


APP_TITLE = "투석환자 일정 체크 도우미"
SAVED_DATA_DIR = Path(".data")
SAVED_DATA_FILE = SAVED_DATA_DIR / "saved_schedule.csv"
PRIVACY_NOTICE = (
    "실제 사용 시 환자 전체 이름, 주민번호, 연락처, 자세한 진단명 등 민감정보 입력을 피하고 "
    "병원 내부 기준에 맞는 최소 정보만 입력하세요."
)

BASE_COLUMNS = [
    "환자 식별 정보",
    "병동 또는 구분",
    "신환 검사일",
    "1개월 검사일",
    "3개월 검사일",
    "6개월 검사일",
    "이번달 처방 날짜",
    "다음 처방 날짜",
    "혈관외과 방문일",
    "혈액검사 특이 소견",
    "비고",
    "확인 상태",
]

DATE_COLUMNS = [
    "신환 검사일",
    "1개월 검사일",
    "3개월 검사일",
    "6개월 검사일",
    "이번달 처방 날짜",
    "다음 처방 날짜",
    "혈관외과 방문일",
]


def setup_page() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="🗓️", layout="wide")
    st.markdown(
        """
        <style>
        .main .block-container { padding-top: 1.6rem; max-width: 1160px; }
        h1 { letter-spacing: 0; }
        .notice {
            border-left: 5px solid #0f766e;
            background: #ecfdf5;
            padding: 0.9rem 1rem;
            border-radius: 8px;
            color: #064e3b;
            margin: 0.4rem 0 1rem 0;
        }
        .schedule-card {
            border: 1px solid #d8dee4;
            border-radius: 8px;
            padding: 0.85rem 1rem;
            margin: 0.45rem 0;
            background: #ffffff;
        }
        .schedule-card strong { color: #0f172a; }
        .small-muted { color: #64748b; font-size: 0.92rem; }
        div[data-testid="stMetricValue"] { font-size: 1.45rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def find_logo_file() -> Path | None:
    logo_keywords = ("logo", "로고", "brand", "icon")
    image_extensions = {".png", ".jpg", ".jpeg", ".webp"}
    for path in Path.cwd().rglob("*"):
        if path.is_file() and path.suffix.lower() in image_extensions:
            lowered_name = path.name.lower()
            if any(keyword in lowered_name for keyword in logo_keywords):
                return path
    return None


def parse_date_value(value) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def format_date_value(value) -> str:
    parsed = parse_date_value(value)
    return parsed.isoformat() if parsed else ""


def create_sample_data() -> pd.DataFrame:
    today = date.today()
    sample_rows = [
        {
            "환자 식별 정보": "김OO",
            "병동 또는 구분": "월수금 오전",
            "신환 검사일": today.isoformat(),
            "1개월 검사일": (today + timedelta(days=7)).isoformat(),
            "3개월 검사일": (today + timedelta(days=21)).isoformat(),
            "6개월 검사일": "",
            "이번달 처방 날짜": today.isoformat(),
            "다음 처방 날짜": (today + timedelta(days=28)).isoformat(),
            "혈관외과 방문일": "",
            "혈액검사 특이 소견": "칼륨 재확인 필요 메모",
            "비고": "오전 회진 전 확인",
            "확인 상태": "확인 전",
        },
        {
            "환자 식별 정보": "이OO",
            "병동 또는 구분": "화목토 오후",
            "신환 검사일": "",
            "1개월 검사일": "",
            "3개월 검사일": (today + timedelta(days=3)).isoformat(),
            "6개월 검사일": (today.replace(day=28) if today.day <= 28 else today).isoformat(),
            "이번달 처방 날짜": (today + timedelta(days=5)).isoformat(),
            "다음 처방 날짜": "",
            "혈관외과 방문일": (today + timedelta(days=2)).isoformat(),
            "혈액검사 특이 소견": "Hb 추적 메모",
            "비고": "보호자 설명 여부 확인",
            "확인 상태": "확인 전",
        },
        {
            "환자 식별 정보": "박OO",
            "병동 또는 구분": "격리실",
            "신환 검사일": "",
            "1개월 검사일": (today - timedelta(days=2)).isoformat(),
            "3개월 검사일": "",
            "6개월 검사일": "",
            "이번달 처방 날짜": "",
            "다음 처방 날짜": (today + timedelta(days=14)).isoformat(),
            "혈관외과 방문일": today.isoformat(),
            "혈액검사 특이 소견": "추가 채혈 결과 대기",
            "비고": "확인 후 상태 변경",
            "확인 상태": "확인 완료",
        },
    ]
    return pd.DataFrame(sample_rows, columns=BASE_COLUMNS)


def normalize_schedule_dataframe(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df.copy()
    df.columns = [str(column).strip() for column in df.columns]
    df = rename_uploaded_columns(df)
    for column in BASE_COLUMNS:
        if column not in df.columns:
            df[column] = ""
    df = df[BASE_COLUMNS]
    for column in DATE_COLUMNS:
        df[column] = df[column].apply(format_date_value)
    df["환자 식별 정보"] = df["환자 식별 정보"].fillna("").astype(str).str.strip()
    df["병동 또는 구분"] = df["병동 또는 구분"].fillna("").astype(str).str.strip()
    df["혈액검사 특이 소견"] = df["혈액검사 특이 소견"].fillna("").astype(str).str.strip()
    df["비고"] = df["비고"].fillna("").astype(str).str.strip()
    df["확인 상태"] = df["확인 상태"].fillna("확인 전").astype(str)
    df.loc[~df["확인 상태"].isin(["확인 전", "확인 완료"]), "확인 상태"] = "확인 전"
    return df


def rename_uploaded_columns(df: pd.DataFrame) -> pd.DataFrame:
    def compact(text: str) -> str:
        return "".join(str(text).lower().replace("\n", " ").split())

    column_rules = {
        "환자 식별 정보": ["환자식별정보", "환자명", "환자이름", "성명", "이름", "환자", "등록번호", "병록번호", "차트번호"],
        "병동 또는 구분": ["병동또는구분", "병동", "구분", "투석반", "스케줄", "요일", "방"],
        "신환 검사일": ["신환검사일", "신환", "초진", "신규"],
        "1개월 검사일": ["1개월검사일", "1개월", "1달", "한달"],
        "3개월 검사일": ["3개월검사일", "3개월", "세달"],
        "6개월 검사일": ["6개월검사일", "6개월", "여섯달"],
        "다음 처방 날짜": ["다음처방날짜", "다음처방", "다음처방일", "차기처방"],
        "이번달 처방 날짜": ["이번달처방날짜", "이번달처방", "이번달처방일", "이번처방", "당월처방"],
        "혈관외과 방문일": ["혈관외과방문일", "혈관외과", "혈관방문", "혈관진료", "혈관"],
        "혈액검사 특이 소견": ["혈액검사특이소견", "특이소견", "검사특이", "혈액검사", "검사메모", "소견"],
        "비고": ["비고", "메모", "참고", "remark", "note"],
        "확인 상태": ["확인상태", "상태", "확인", "완료여부"],
    }
    rename_map = {}
    used_targets = set()
    for source_column in df.columns:
        source_key = compact(source_column)
        for target_column, candidates in column_rules.items():
            if target_column in used_targets:
                continue
            if source_key == compact(target_column) or any(candidate in source_key for candidate in candidates):
                rename_map[source_column] = target_column
                used_targets.add(target_column)
                break
    return df.rename(columns=rename_map)


def find_excel_header_row(uploaded_file, sheet_name, engine: str | None) -> int:
    uploaded_file.seek(0)
    preview_df = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=None, nrows=10, engine=engine)
    keywords = ["환자", "성명", "이름", "병동", "신환", "1개월", "3개월", "6개월", "처방", "혈관", "비고"]
    for index, row in preview_df.iterrows():
        row_text = " ".join(str(value) for value in row.dropna().tolist())
        matched_count = sum(keyword in row_text for keyword in keywords)
        if matched_count >= 2:
            return int(index)
    return 0


def read_excel_schedule(uploaded_file, suffix: str) -> pd.DataFrame:
    engine = "openpyxl" if suffix == ".xlsx" else "xlrd"
    uploaded_file.seek(0)
    excel_file = pd.ExcelFile(uploaded_file, engine=engine)
    frames = []
    for sheet_name in excel_file.sheet_names:
        header_row = find_excel_header_row(uploaded_file, sheet_name, engine)
        uploaded_file.seek(0)
        sheet_df = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=header_row, engine=engine)
        sheet_df = sheet_df.dropna(how="all")
        sheet_df = sheet_df.loc[:, ~sheet_df.columns.astype(str).str.startswith("Unnamed")]
        if not sheet_df.empty:
            frames.append(sheet_df)
    if not frames:
        return empty_schedule_dataframe()
    return pd.concat(frames, ignore_index=True)


def empty_schedule_dataframe() -> pd.DataFrame:
    return pd.DataFrame(columns=BASE_COLUMNS)


def dataframe_to_storage_text(df: pd.DataFrame) -> str:
    normalized_df = normalize_schedule_dataframe(df)
    return normalized_df.to_json(orient="records", force_ascii=False)


def dataframe_from_storage_text(saved_text: str | None) -> pd.DataFrame:
    if not saved_text:
        return empty_schedule_dataframe()
    try:
        loaded_df = pd.read_json(StringIO(saved_text), dtype=False)
        return normalize_schedule_dataframe(loaded_df)
    except Exception:
        return empty_schedule_dataframe()


def save_schedules_to_file(df: pd.DataFrame) -> None:
    SAVED_DATA_DIR.mkdir(exist_ok=True)
    normalize_schedule_dataframe(df).to_csv(SAVED_DATA_FILE, index=False, encoding="utf-8-sig")


def load_schedules_from_file() -> pd.DataFrame:
    if not SAVED_DATA_FILE.exists():
        return empty_schedule_dataframe()
    try:
        return normalize_schedule_dataframe(pd.read_csv(SAVED_DATA_FILE))
    except Exception:
        return empty_schedule_dataframe()


def persist_current_schedules() -> None:
    schedules_df = normalize_schedule_dataframe(st.session_state.schedules)
    save_schedules_to_file(schedules_df)


def initialize_state() -> None:
    if "schedules" not in st.session_state:
        saved_df = load_schedules_from_file()
        st.session_state.schedules = saved_df if not saved_df.empty else empty_schedule_dataframe()


def add_schedule(row: dict[str, str]) -> None:
    new_row = pd.DataFrame([row], columns=BASE_COLUMNS)
    st.session_state.schedules = normalize_schedule_dataframe(
        pd.concat([st.session_state.schedules, new_row], ignore_index=True)
    )


def read_uploaded_schedule(uploaded_file) -> pd.DataFrame:
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix == ".csv":
        try:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, encoding="utf-8-sig")
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, encoding="cp949")
    if suffix in {".xlsx", ".xls"}:
        return read_excel_schedule(uploaded_file, suffix)
    raise ValueError("CSV 또는 Excel 파일만 불러올 수 있습니다.")


def schedule_events(df: pd.DataFrame) -> pd.DataFrame:
    events = []
    for _, row in df.iterrows():
        for schedule_type in DATE_COLUMNS:
            schedule_date = parse_date_value(row.get(schedule_type))
            if schedule_date:
                events.append(
                    {
                        "환자 식별 정보": row["환자 식별 정보"],
                        "병동 또는 구분": row["병동 또는 구분"],
                        "일정 종류": schedule_type,
                        "일정 날짜": schedule_date.isoformat(),
                        "혈액검사 특이 소견": row["혈액검사 특이 소견"],
                        "비고": row["비고"],
                        "확인 상태": row["확인 상태"],
                    }
                )
    if not events:
        return pd.DataFrame(
            columns=[
                "환자 식별 정보",
                "병동 또는 구분",
                "일정 종류",
                "일정 날짜",
                "혈액검사 특이 소견",
                "비고",
                "확인 상태",
            ]
        )
    return pd.DataFrame(events).sort_values(["일정 날짜", "환자 식별 정보"])


def filter_today_events(events_df: pd.DataFrame) -> pd.DataFrame:
    today_text = date.today().isoformat()
    if events_df.empty:
        return events_df
    return events_df[events_df["일정 날짜"] == today_text]


def filter_this_month_events(events_df: pd.DataFrame) -> pd.DataFrame:
    if events_df.empty:
        return events_df
    month_prefix = date.today().strftime("%Y-%m")
    return events_df[events_df["일정 날짜"].astype(str).str.startswith(month_prefix)]


def filter_upcoming_events(events_df: pd.DataFrame, days: int = 7) -> pd.DataFrame:
    if events_df.empty:
        return events_df
    today = date.today()
    limit = today + timedelta(days=days)
    mask = events_df["일정 날짜"].apply(
        lambda value: (parsed := parse_date_value(value)) is not None and today <= parsed <= limit
    )
    return events_df[mask].head(8)


def make_csv_download(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")


def make_txt_summary(events_df: pd.DataFrame) -> str:
    if events_df.empty:
        return "등록된 일정이 없습니다."
    lines = [f"{APP_TITLE} 전체 일정 요약", f"생성일: {date.today().isoformat()}", ""]
    for _, event in events_df.iterrows():
        lines.append(
            f"- {event['일정 날짜']} | {event['환자 식별 정보']} | {event['일정 종류']} | "
            f"{event['병동 또는 구분']} | {event['확인 상태']} | {event['비고']}"
        )
    return "\n".join(lines)


def render_header() -> None:
    logo_file = find_logo_file()
    if logo_file:
        left, right = st.columns([1, 5])
        with left:
            st.image(str(logo_file), width=92)
        with right:
            st.title(APP_TITLE)
            st.caption("투석환자별 검사일, 처방일, 혈관외과 방문일, 혈액검사 특이 소견, 비고를 모바일에서도 간단히 메모하고 한눈에 확인하는 일정 체크 앱입니다.")
    else:
        st.title(APP_TITLE)
        st.caption("투석환자별 검사일, 처방일, 혈관외과 방문일, 혈액검사 특이 소견, 비고를 모바일에서도 간단히 메모하고 한눈에 확인하는 일정 체크 앱입니다.")
    st.markdown(f"<div class='notice'><strong>개인정보 보호 안내</strong><br>{PRIVACY_NOTICE}</div>", unsafe_allow_html=True)
    st.info("이 앱은 일정 메모와 확인용 도구입니다. 의료 판단, 진단, 처방 추천, 처방 변경을 하지 않습니다.")


def render_input_form() -> None:
    st.subheader("환자 일정 입력")
    with st.form("schedule_form", clear_on_submit=False):
        patient_id = st.text_input("환자 이름 또는 최소 식별 정보", placeholder="예: 김OO, 3병동 A-12")
        ward = st.text_input("병동 또는 구분", placeholder="예: 월수금 오전, 5병동")

        st.markdown("검사일과 처방일")
        new_patient_date = st.date_input("신환 검사일", value=None)
        one_month_date = st.date_input("1개월 검사일", value=None)
        three_month_date = st.date_input("3개월 검사일", value=None)
        six_month_date = st.date_input("6개월 검사일", value=None)
        current_prescription_date = st.date_input("이번달 처방 날짜", value=None)
        next_prescription_date = st.date_input("다음 처방 날짜", value=None)
        vascular_visit_date = st.date_input("혈관외과 방문일", value=None)

        lab_note = st.text_area("혈액검사 특이 소견", placeholder="검사 결과 해석이 아니라 확인해야 할 메모만 적어 주세요.")
        memo = st.text_area("비고", placeholder="예: 회진 전 확인, 보호자 설명 여부 확인")
        status = st.radio("확인 상태", ["확인 전", "확인 완료"], horizontal=True)
        submitted = st.form_submit_button("일정 추가", type="primary")

    if submitted:
        has_any_date = any(
            [
                new_patient_date,
                one_month_date,
                three_month_date,
                six_month_date,
                current_prescription_date,
                next_prescription_date,
                vascular_visit_date,
            ]
        )
        if not patient_id.strip():
            st.warning("환자 전체 이름 대신 비식별 정보나 최소 식별 정보를 입력해 주세요.")
        elif not has_any_date:
            st.warning("최소 1개 이상의 검사일, 처방 날짜, 방문일을 입력해 주세요.")
        else:
            add_schedule(
                {
                    "환자 식별 정보": patient_id.strip(),
                    "병동 또는 구분": ward.strip(),
                    "신환 검사일": format_date_value(new_patient_date),
                    "1개월 검사일": format_date_value(one_month_date),
                    "3개월 검사일": format_date_value(three_month_date),
                    "6개월 검사일": format_date_value(six_month_date),
                    "이번달 처방 날짜": format_date_value(current_prescription_date),
                    "다음 처방 날짜": format_date_value(next_prescription_date),
                    "혈관외과 방문일": format_date_value(vascular_visit_date),
                    "혈액검사 특이 소견": lab_note.strip(),
                    "비고": memo.strip(),
                    "확인 상태": status,
                }
            )
            persist_current_schedules()
            st.success("일정이 전체 환자 일정표에 추가되고 저장되었습니다.")


def render_file_tools() -> None:
    st.subheader("저장 및 파일 불러오기")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("저장된/과거 일정 불러오기", width="stretch"):
            file_df = load_schedules_from_file()
            loaded_df = file_df
            if loaded_df.empty:
                st.warning("아직 저장된 일정이 없습니다. 일정을 추가한 뒤 저장하거나 CSV/Excel 파일을 업로드해 주세요.")
            else:
                st.session_state.schedules = loaded_df
                save_schedules_to_file(loaded_df)
                st.success(f"저장된 과거 일정 {len(loaded_df)}건을 불러왔습니다.")
    with col2:
        if st.button("현재 일정 저장하기", width="stretch", disabled=st.session_state.schedules.empty):
            persist_current_schedules()
            st.success(f"현재 일정 {len(st.session_state.schedules)}건을 저장했습니다.")

    col3, col4 = st.columns(2)
    with col3:
        if st.button("전체 일정 비우기", width="stretch"):
            st.session_state.schedules = empty_schedule_dataframe()
            st.success("화면의 일정표를 비웠습니다. 저장된 과거 데이터는 삭제하지 않았습니다.")
    with col4:
        if st.button("테스트용 샘플 보기", width="stretch"):
            st.session_state.schedules = create_sample_data()
            st.info("테스트용 비식별 샘플 3건을 불러왔습니다. 실제 저장 데이터로 쓰려면 현재 일정 저장하기를 눌러 주세요.")

    uploaded_file = st.file_uploader("CSV 또는 Excel 일정 파일 업로드", type=["csv", "xlsx", "xls"])
    if uploaded_file:
        try:
            uploaded_df = normalize_schedule_dataframe(read_uploaded_schedule(uploaded_file))
            st.session_state.schedules = normalize_schedule_dataframe(
                pd.concat([st.session_state.schedules, uploaded_df], ignore_index=True)
            )
            persist_current_schedules()
            st.success(f"{uploaded_file.name} 파일에서 {len(uploaded_df)}건을 불러오고 저장했습니다.")
        except Exception:
            st.error(
                "파일을 읽지 못했습니다. 예전 엑셀(.xls), 최신 엑셀(.xlsx), CSV 파일을 지원합니다. "
                "계속 안 되면 파일을 Excel에서 열어 .xlsx로 다시 저장한 뒤 업로드해 주세요."
            )


def render_event_cards(events_df: pd.DataFrame, empty_message: str) -> None:
    if events_df.empty:
        st.write(empty_message)
        return
    for _, event in events_df.iterrows():
        st.markdown(
            f"""
            <div class="schedule-card">
                <strong>{event['일정 날짜']} · {event['일정 종류']}</strong><br>
                {event['환자 식별 정보']} / {event['병동 또는 구분']} / {event['확인 상태']}<br>
                <span class="small-muted">특이 소견: {event['혈액검사 특이 소견'] or '-'} · 비고: {event['비고'] or '-'}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_dashboard() -> None:
    schedules_df = normalize_schedule_dataframe(st.session_state.schedules)
    events_df = schedule_events(schedules_df)
    today_events = filter_today_events(events_df)
    month_events = filter_this_month_events(events_df)
    upcoming_events = filter_upcoming_events(events_df)

    total_patients = len(schedules_df)
    pending_count = int((schedules_df["확인 상태"] == "확인 전").sum()) if not schedules_df.empty else 0
    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("등록 환자 일정", f"{total_patients}건")
    metric2.metric("오늘 확인", f"{len(today_events)}건")
    metric3.metric("이번 달 일정", f"{len(month_events)}건")
    metric4.metric("확인 전", f"{pending_count}건")

    st.subheader("오늘 확인해야 할 목록")
    render_event_cards(today_events, "오늘 날짜와 일치하는 일정이 아직 없습니다.")

    st.subheader("가까운 일정")
    render_event_cards(upcoming_events, "앞으로 7일 안에 표시할 일정이 없습니다.")

    st.subheader("이번 달 전체 일정표")
    if month_events.empty:
        st.write("이번 달에 해당하는 일정이 아직 없습니다.")
    else:
        st.dataframe(month_events, width="stretch", hide_index=True)

    st.subheader("전체 환자 일정표")
    search_text = st.text_input("환자 식별 정보 또는 병동 검색", placeholder="예: 김OO, 월수금")
    status_filter = st.selectbox("확인 상태 필터", ["전체", "확인 전", "확인 완료"])
    visible_df = schedules_df.copy()
    if search_text.strip():
        keyword = search_text.strip()
        visible_df = visible_df[
            visible_df["환자 식별 정보"].str.contains(keyword, case=False, na=False)
            | visible_df["병동 또는 구분"].str.contains(keyword, case=False, na=False)
        ]
    if status_filter != "전체":
        visible_df = visible_df[visible_df["확인 상태"] == status_filter]

    if visible_df.empty:
        st.write("표시할 일정이 없습니다. 직접 입력하거나 샘플 일정을 불러와 주세요.")
    else:
        st.dataframe(visible_df, width="stretch", hide_index=True)

    st.subheader("다운로드")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "전체 일정 CSV 다운로드",
            data=make_csv_download(schedules_df),
            file_name="dialysis_schedule.csv",
            mime="text/csv",
            width="stretch",
            disabled=schedules_df.empty,
        )
    with col2:
        st.download_button(
            "전체 일정 TXT 요약 다운로드",
            data=make_txt_summary(events_df),
            file_name="dialysis_schedule_summary.txt",
            mime="text/plain",
            width="stretch",
            disabled=events_df.empty,
        )


def main() -> None:
    setup_page()
    initialize_state()
    render_header()

    left, right = st.columns([1, 1], gap="large")
    with left:
        render_input_form()
        render_file_tools()
    with right:
        render_dashboard()


if __name__ == "__main__":
    main()
