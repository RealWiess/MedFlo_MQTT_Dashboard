@echo off
set PATH=C:\SW code\source code\ITE9868_GWBuild_20260705\tool\bin;C:\ITEGCC_98x\bin;%PATH%
set CFG_PROJECT=GW202601
set CFG_PLATFORM=openrtos
set CFG_BUILDPLATFORM=openrtos
set CMAKE_SOURCE_DIR=C:\SW code\source code\ITE9868_GWBuild_20260705
cd /d "C:\SW code\source code\ITE9868_GWBuild_20260705\build\openrtos\GW202601"
if exist CMakeCache.txt del CMakeCache.txt
echo Running CMake...
cmake -G"Unix Makefiles" -DCMAKE_TOOLCHAIN_FILE="C:\SW code\source code\ITE9868_GWBuild_20260705\openrtos\toolchain.cmake" "C:\SW code\source code\ITE9868_GWBuild_20260705"
echo Running Make...
make
