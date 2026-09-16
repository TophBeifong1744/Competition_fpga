# Included by the user at the END of the existing application CMakeLists.txt.
# Does not compile or operate hardware itself. Guards the user's Vitis Build.
if(NOT TARGET ${APP_NAME}.elf)
  message(FATAL_ERROR "Include C1 gate after the application target is defined")
endif()
set(C1_PYTHON "C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe" CACHE FILEPATH "Python 3.11+; configurable")
get_filename_component(C1_APP "${CMAKE_CURRENT_SOURCE_DIR}/.." ABSOLUTE)
set(C1_PLATFORM "${C1_APP}/../continuous_platform" CACHE PATH "Existing continuous platform")
set(C1_RECORD_ROOT "${C1_APP}/c1_checks" CACHE PATH "Append-only check records, outside build/clean")
get_filename_component(C1_TOOLS "${CMAKE_C_COMPILER}" DIRECTORY)
if(NOT EXISTS "${C1_PYTHON}")
  message(FATAL_ERROR "Set C1_PYTHON to an existing Python 3.11+ executable")
endif()
set(C1_CHECK_ARGS "${C1_PYTHON}" -B "${CMAKE_CURRENT_LIST_DIR}/check_entry.py"
  --app "${C1_APP}" --platform "${C1_PLATFORM}" --tools-bin "${C1_TOOLS}" --record-root "${C1_RECORD_ROOT}")
add_custom_target(c1_source_guard
  COMMAND ${C1_CHECK_ARGS} --stage pre
  COMMENT "C1: reject old source or mismatched dependencies before compiling" VERBATIM)
add_dependencies(${APP_NAME}.elf c1_source_guard)
add_custom_command(TARGET ${APP_NAME}.elf POST_BUILD
  COMMAND ${C1_CHECK_ARGS} --stage post
  COMMENT "C1: verify actual object/ELF timer, RX contract, map and load paths" VERBATIM)
