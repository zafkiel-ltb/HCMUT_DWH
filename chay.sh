#!/usr/bin/env bash
# Chạy dự án CompanyX DSS trên macOS hoặc Linux. Bản Windows: chay.bat
#   ./chay.sh caidat     tạo .venv và cài thư viện
#   ./chay.sh phan_tich  chạy chuỗi phân tích cum3b -> cum4b -> cum4c -> cum5 -> cum6 -> cum6b (cần data/*.csv)
#   ./chay.sh bao_cao    sinh bảng, hình cho báo cáo rồi biên dịch latex/main.pdf
#   ./chay.sh app        mở giao diện DSS (Streamlit, cổng 8501)
#   ./chay.sh tat_ca     caidat + phan_tich + bao_cao
set -e
cd "$(dirname "$0")"
PY=.venv/bin/python
for d in "$HOME/Library/TinyTeX/bin/universal-darwin" "$HOME/.TinyTeX/bin/x86_64-linux"; do [ -d "$d" ] && PATH="$d:$PATH"; done

caidat() {
  [ -d .venv ] || python3 -m venv .venv
  $PY -m pip install -q -r python/requirements.txt
  echo "Môi trường sẵn sàng: $($PY --version)"
}

phan_tich() {
  for f in snapshot orders lines; do
    [ -f data/$f.csv ] || { echo "Thiếu data/$f.csv. Trích từ kho CompanyX_DW bằng python/kiem_chung/extract.sql rồi chạy lại."; exit 1; }
  done
  $PY python/phan_tich/cum3b_nhan_va_dac_trung.py
  if [ -f models/nb_T20140301.joblib ]; then
    echo "Đã có models/*.joblib, bỏ qua cum4_huan_luyen (chạy tay nếu thật sự muốn huấn luyện lại)."
  else
    $PY python/phan_tich/cum4_huan_luyen.py
  fi
  for s in cum4b_bo_sung_chuong3 cum4c_du_dia cum5_cham_diem_sinh_sql cum6_phan_tich_dss cum6b_bo_sung_chuong3; do
    echo "== $s"; $PY python/phan_tich/$s.py
  done
  echo "Xong chuỗi phân tích. Kết quả trong results/. Ba file SQL trong results/cum5 và results/cum6 chạy trong SSMS để ghi vào kho."
}

bao_cao() {
  for s in tao_bang_tex_etl tao_bang_tex_eda tao_bang_tex_mohinh tao_bang_tex_dss ve_so_do_etl ve_luoc_do_sao ve_hinh_eda ve_hinh_mohinh ve_hinh_dss; do
    echo "== $s"; $PY python/bao_cao/$s.py >/dev/null
  done
  if command -v pdflatex >/dev/null; then
    (cd latex && for i in 1 2 3; do pdflatex -interaction=nonstopmode main.tex >/dev/null; done)
    echo "Đã biên dịch latex/main.pdf (lỗi: $(grep -a -c '^! ' latex/main.log))"
  else
    echo "Không có pdflatex, bỏ qua biên dịch. Nén thư mục latex/ đưa lên Overleaf hoặc cài TinyTeX."
  fi
}

app() { exec $PY -m streamlit run python/app_dss.py --server.port 8501; }

case "${1:-}" in
  caidat) caidat ;;
  phan_tich) phan_tich ;;
  bao_cao) bao_cao ;;
  app) app ;;
  tat_ca) caidat; phan_tich; bao_cao ;;
  *) sed -n '2,7p' "$0"; exit 1 ;;
esac
