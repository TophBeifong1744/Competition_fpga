# Included by the user at the END of the existing application CMakeLists.txt.
# Does not compile or operate hardware itself. Guards the user's Vitis Build.
if(NOT TARGET ${APP_NAME}.elf)
  message(FATAL_ERROR "Include E1 gate after the application target is defined")
endif()
set(E1_PYTHON "C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe" CACHE FILEPATH "Python 3.11+; configurable")
get_filename_component(E1_APP "${CMAKE_CURRENT_SOURCE_DIR}/.." ABSOLUTE)
set(E1_PLATFORM "${E1_APP}/../continuous_platform" CACHE PATH "Existing continuous platform")
set(E1_RECORD_ROOT "${E1_APP}/e1_checks" CACHE PATH "Append-only check records, outside build/clean")
get_filename_component(E1_TOOLS "${CMAKE_C_COMPILER}" DIRECTORY)
if(NOT EXISTS "${E1_PYTHON}")
  message(FATAL_ERROR "Set E1_PYTHON to an existing Python 3.11+ executable")
endif()
set(E1_CHECK_ARGS "${E1_PYTHON}" -B "${CMAKE_CURRENT_LIST_DIR}/check_endurance.py"
  --app "${E1_APP}" --platform "${E1_PLATFORM}" --tools-bin "${E1_TOOLS}" --record-root "${E1_RECORD_ROOT}")
add_custom_target(e1_source_guard
  COMMAND ${E1_CHECK_ARGS} --stage pre
  COMMENT "E1: reject old source or mismatched dependencies before compiling" VERBATIM)
add_dependencies(${APP_NAME}.elf e1_source_guard)
add_custom_command(TARGET ${APP_NAME}.elf POST_BUILD
  COMMAND ${E1_CHECK_ARGS} --stage post
  COMMENT "E1: verify actual object/ELF timer, RX contract, map and session schedule" VERBATIM)
