"""
predict.py — 채무불이행 예측 추론 모듈

pipeline.pkl 을 로드하고 입력값을 받아 예측 결과를 반환합니다.
파이프라인 내부 순서: StandardScaler → PCA(15) → SMOTE → RFC
"""

import joblib
import pandas as pd
from pathlib import Path

# ── 모델 로드 (모듈 임포트 시 1회만 실행) ──────────────────────────
MODEL_PATH = Path(__file__).parent / "models" / "pipeline.pkl"
pipeline   = joblib.load(MODEL_PATH)

# ── 피처 컬럼 순서 (학습 시와 동일하게 유지) ──────────────────────
FEATURE_COLS = [
    'LIMIT_BAL', 'SEX', 'EDUCATION', 'MARRIAGE', 'AGE',
    'PAY_0',  'PAY_2',  'PAY_3',  'PAY_4',  'PAY_5',  'PAY_6',
    'BILL_AMT1', 'BILL_AMT2', 'BILL_AMT3',
    'BILL_AMT4', 'BILL_AMT5', 'BILL_AMT6',
    'PAY_AMT1',  'PAY_AMT2',  'PAY_AMT3',
    'PAY_AMT4',  'PAY_AMT5',  'PAY_AMT6',
]


def predict(input_dict: dict) -> dict:
    """
    단일 고객 데이터로 채무불이행 확률과 예측 클래스를 반환합니다.

    Parameters
    ----------
    input_dict : dict
        피처명: 값 딕셔너리 (23개 피처, FEATURE_COLS 순서 무관)

    Returns
    -------
    dict
        prob   (float) : 채무불이행 확률  0.0 ~ 1.0
        label  (int)   : 예측 클래스  0=정상 / 1=채무불이행
        result (str)   : 한국어 결과 문자열
    """
    df    = pd.DataFrame([input_dict], columns=FEATURE_COLS)
    prob  = float(pipeline.predict_proba(df)[0][1])
    label = int(pipeline.predict(df)[0])

    return {
        "prob"  : round(prob, 4),
        "label" : label,
        "result": "채무불이행 위험" if label == 1 else "정상",
    }


# ── app1.py 용 추가 함수 ─────────────────────────────────────────

# 위험등급 기준표 (FR-05)
RISK_LEVELS = [
    (0.7, "위험", "🔴", "한도 정지 / 추심 검토",  "error"),
    (0.5, "경고", "🟠", "한도 축소 검토",          "warning"),
    (0.3, "주의", "🟡", "모니터링 필요",            "warning"),
    (0.0, "안전", "🟢", "한도 증액 가능",           "success"),
]

def load_pipeline():
    """EX-01 대응 — 파일 없으면 FileNotFoundError 발생"""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {MODEL_PATH}")
    return joblib.load(MODEL_PATH)

def get_risk(prob: float) -> dict:
    """확률 → 위험등급·아이콘·권장조치 반환 (FR-05)"""
    for threshold, level, icon, action, msg_type in RISK_LEVELS:
        if prob >= threshold:
            return {"level": level, "icon": icon,
                    "action": action, "msg_type": msg_type}


# ── 단독 실행 시 동작 테스트 ─────────────────────────────────────
if __name__ == "__main__":
    sample = {
        'LIMIT_BAL': 20000,  'SEX': 2, 'EDUCATION': 2, 'MARRIAGE': 1, 'AGE': 24,
        'PAY_0': 2,  'PAY_2': 2,  'PAY_3': -1, 'PAY_4': -1, 'PAY_5': -2, 'PAY_6': -2,
        'BILL_AMT1': 3913, 'BILL_AMT2': 3102, 'BILL_AMT3': 689,
        'BILL_AMT4': 0,    'BILL_AMT5': 0,    'BILL_AMT6': 0,
        'PAY_AMT1': 0,   'PAY_AMT2': 689,  'PAY_AMT3': 0,
        'PAY_AMT4': 0,   'PAY_AMT5': 0,    'PAY_AMT6': 0,
    }
    result = predict(sample)
    print(f"채무불이행 확률 : {result['prob']:.4f}")
    print(f"예측 클래스     : {result['label']}  ({result['result']})")
