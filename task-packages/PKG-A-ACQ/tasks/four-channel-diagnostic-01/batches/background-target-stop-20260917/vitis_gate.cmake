# Included by the user at the END of the existing application CMakeLists.txt.
# Does not compile or operate hardware itself. Guards the user's Vitis Build.
if(NOT TARGET ${APP_NAME}.elf)
  message(FATAL_ERROR "Include S1 gate after the application target is defined")
endif()
set(S1_PYTHON "C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe" CACHE FILEPATH "Python 3.11+; configurable")
get_filename_component(S1_APP "${CMAKE_CURRENT_SOURCE_DIR}/.." ABSOLUTE)
set(S1_PLATFORM "${S1_APP}/../continuous_platform" CACHE PATH "Existing continuous platform")
set(S1_RECORD_ROOT "${S1_APP}/scene_checks" CACHE PATH "Append-only check records, outside build/clean")
get_filename_component(S1_TOOLS "${CMAKE_C_COMPILER}" DIRECTORY)
if(NOT EXISTS "${S1_PYTHON}")
  message(FATAL_ERROR "Set S1_PYTHON to an existing Python 3.11+ executable")
endif()
set(S1_CHECK_ARGS "${S1_PYTHON}" -B "${CMAKE_CURRENT_LIST_DIR}/check_scene.py"
  --app "${S1_APP}" --platform "${S1_PLATFORM}" --tools-bin "${S1_TOOLS}" --record-root "${S1_RECORD_ROOT}")
add_custom_target(s1_source_guard
  COMMAND ${S1_CHECK_ARGS} --stage pre
  COMMENT "S1: reject old source or mismatched dependencies before compiling" VERBATIM)
add_dependencies(${APP_NAME}.elf s1_source_guard)
add_custom_command(TARGET ${APP_NAME}.elf POST_BUILD
  COMMAND ${S1_CHECK_ARGS} --stage post
  COMMENT "S1: verify actual object/ELF timer, RX/archive contract, map and six-second profile" VERBATIM)
