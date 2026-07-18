@echo off
set PATH=C:\SW code\source code\ITE9868_Build_20260704\tool\bin;C:\ITEGCC_98x\bin;%PATH%
set CFG_PROJECT=GW202601
set CFG_PLATFORM=openrtos
set CFG_BUILDPLATFORM=openrtos
set CMAKE_SOURCE_DIR=C:\SW code\source code\ITE9868_Build_20260704
cd /d "C:\SW code\source code\ITE9868_Build_20260704\build\openrtos\GW202601"
cmake -G"Unix Makefiles" -DCMAKE_TOOLCHAIN_FILE="C:\SW code\source code\ITE9868_Build_20260704\openrtos\toolchain.cmake" "C:\SW code\source code\ITE9868_Build_20260704" > cmake_cmd_output.log 2>&1
