# Rewritten based on FindJsonCpp module that is found in CMake sources
#
# See
# https://gitlab.kitware.com/cmake/cmake/blob/master/Source/Modules/FindJsonCpp.cmake
# for the original module
#

find_library(JsonCpp_LIBRARY NAMES jsoncpp)
mark_as_advanced(JsonCpp_LIBRARY)

find_path(JsonCpp_INCLUDE_DIR NAMES json/json.h PATH_SUFFIXES jsoncpp)
mark_as_advanced(JsonCpp_INCLUDE_DIR)

set(_JsonCpp_VERSION_FILE "${JsonCpp_INCLUDE_DIR}/json/version.h")

if(JsonCpp_INCLUDE_DIR AND EXISTS "${_JsonCpp_VERSION_FILE}")
    file(
        STRINGS "${_JsonCpp_VERSION_FILE}"
        _JsonCpp_VERSION_DEFS
        REGEX "^#[ ]?define JSONCPP_VERSION"
    )
endif()

if(_JsonCpp_VERSION_DEFS)
    string(REGEX REPLACE
        "^.*#[ ]?define JSONCPP_VERSION_MAJOR ([0-9]+).*$" "\\1"
        JsonCpp_VERSION_MAJOR "${_JsonCpp_VERSION_DEFS}"
    )
    string(REGEX REPLACE
        "^.*#[ ]?define JSONCPP_VERSION_MINOR ([0-9]+).*$" "\\1"
        JsonCpp_VERSION_MINOR "${_JsonCpp_VERSION_DEFS}"
    )
    string(REGEX REPLACE
        "^.*#[ ]?define JSONCPP_VERSION_PATCH ([0-9]+).*$" "\\1"
        JsonCpp_VERSION_PATCH "${_JsonCpp_VERSION_DEFS}"
    )
    string(REGEX REPLACE
        "^.*#[ ]?define JSONCPP_VERSION_STRING \"([0-9\\.]+)\".*$" "\\1"
        JsonCpp_VERSION_STRING "${_JsonCpp_VERSION_DEFS}"
    )
    unset(_JsonCpp_VERSION_DEFS)
else()
    set(JsonCpp_VERSION_MAJOR "")
    set(JsonCpp_VERSION_MINOR "")
    set(JsonCpp_VERSION_PATCH "")
    set(JsonCpp_VERSION_STRING "")
endif()

unset(_JsonCpp_VERSION_FILE)

include(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(
    JsonCpp
    FOUND_VAR JsonCpp_FOUND
    REQUIRED_VARS JsonCpp_LIBRARY JsonCpp_INCLUDE_DIR
    VERSION_VAR JsonCpp_VERSION_STRING
)

if(JsonCpp_FOUND)
    if(NOT TARGET JsonCpp::JsonCpp)
        add_library(JsonCpp::JsonCpp UNKNOWN IMPORTED)
        set_target_properties(
            JsonCpp::JsonCpp PROPERTIES
            IMPORTED_LOCATION "${JsonCpp_LIBRARY}"
            INTERFACE_INCLUDE_DIRECTORIES "${JsonCpp_INCLUDE_DIR}"
            IMPORTED_LINK_INTERFACE_LANGUAGES "CXX"
        )
    endif()
endif()
