[app]
title = PetApp
package.name = petapp
package.domain = org.example
source.dir = .
source.include_exts = py,tflite
version = 1.0

# Зависимости Python
requirements = python3, kivy, tensorflow-lite, ipfshttpclient, requests, android

# Дополнительные JAR-файлы (если используешь .aar для TFLite, иначе можно убрать)
android.add_jars = libs/tensorflow-lite.aar

# Пути к заголовкам и библиотекам (для Termux)
android.add_include_paths = /data/data/com.termux/files/usr/include
android.add_libs_arm64-v8a = /data/data/com.termux/files/usr/lib/libz.so
android.add_compile_options = -I/data/data/com.termux/files/usr/include
android.add_link_options = -L/data/data/com.termux/files/usr/lib

# Разрешения Android
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, ACCESS_NETWORK_STATE

# Настройки Android API и NDK
android.api = 31
android.minapi = 21
android.sdk = /data/data/com.termux/files/home/android-sdk
android.ndk_path = /data/data/com.termux/files/home/.buildozer/android/platform/android-ndk
android.ndk_version = 25.2.9519653
android.archs = arm64-v8a

# Пропуск проверки zlib (он уже есть в Termux)
android.skip_deps_check = zlib

# Путь к Python-for-Android
p4a.source_dir = /data/data/com.termux/files/home/.buildozer/android/platform/python-for-android

# Дополнительные настройки сборки
android.accept_sdk_license = True
android.bootstrap = sdl2  # Для Kivy с графическим интерфейсом
log_level = 2
warn_on_root = 0
