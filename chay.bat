@echo off
rem Chạy dự án CompanyX DSS trên Windows. Bản macOS/Linux: chay.sh
rem   chay caidat     tạo .venv và cài thư viện
rem   chay phan_tich  chạy chuỗi phân tích cum3b -> cum4b -> cum4c -> cum5 -> cum6 -> cum6b (cần data\*.csv)
rem   chay bao_cao    sinh bảng, hình cho báo cáo rồi biên dịch latex\main.pdf
rem   chay app        mở giao diện DSS (Streamlit, cổng 8501)
rem   chay tat_ca     caidat + phan_tich + bao_cao
setlocal
cd /d "%~dp0"
set PY=.venv\Scripts\python.exe

if "%1"=="caidat" goto caidat
if "%1"=="phan_tich" goto phan_tich
if "%1"=="bao_cao" goto bao_cao
if "%1"=="app" goto app
if "%1"=="tat_ca" goto tat_ca
echo Cach dung: chay caidat ^| phan_tich ^| bao_cao ^| app ^| tat_ca
exit /b 1

:caidat
if not exist .venv py -3 -m venv .venv || exit /b 1
%PY% -m pip install -q -r python\requirements.txt || exit /b 1
%PY% --version
goto :eof

:phan_tich
for %%f in (snapshot orders lines) do if not exist data\%%f.csv (
  echo Thieu data\%%f.csv. Trich tu kho CompanyX_DW bang python\kiem_chung\extract.sql roi chay lai.
  exit /b 1
)
%PY% python\phan_tich\cum3b_nhan_va_dac_trung.py || exit /b 1
if exist models\nb_T20140301.joblib (
  echo Da co models\*.joblib, bo qua cum4_huan_luyen.
) else (
  %PY% python\phan_tich\cum4_huan_luyen.py || exit /b 1
)
for %%s in (cum4b_bo_sung_chuong3 cum4c_du_dia cum5_cham_diem_sinh_sql cum6_phan_tich_dss cum6b_bo_sung_chuong3) do (
  echo == %%s
  %PY% python\phan_tich\%%s.py || exit /b 1
)
echo Xong chuoi phan tich. Ket qua trong results\.
goto :eof

:bao_cao
for %%s in (tao_bang_tex_etl tao_bang_tex_eda tao_bang_tex_mohinh tao_bang_tex_dss ve_so_do_etl ve_luoc_do_sao ve_hinh_eda ve_hinh_mohinh ve_hinh_dss) do (
  echo == %%s
  %PY% python\bao_cao\%%s.py >nul || exit /b 1
)
where pdflatex >nul 2>nul
if errorlevel 1 (
  echo Khong co pdflatex, bo qua bien dich. Nen thu muc latex\ dua len Overleaf hoac cai MiKTeX.
) else (
  pushd latex
  for %%i in (1 2 3) do pdflatex -interaction=nonstopmode main.tex >nul
  popd
  echo Da bien dich latex\main.pdf
)
goto :eof

:app
%PY% -m streamlit run python\app_dss.py --server.port 8501
goto :eof

:tat_ca
call :caidat || exit /b 1
call :phan_tich || exit /b 1
call :bao_cao
goto :eof
