import os

def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content.strip() + "\n")

# Project Root
ROOT = "PizzaClubOS"

# 1. Root settings.gradle.kts
create_file(f"{ROOT}/settings.gradle.kts", """
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        maven { url = uri("https://jitpack.io") }
    }
}
rootProject.name = "PizzaClubOS"
include(":app")
""")

# 2. Root build.gradle.kts
create_file(f"{ROOT}/build.gradle.kts", """
plugins {
    id("com.android.application") version "8.1.0" apply false
    id("org.jetbrains.kotlin.android") version "1.9.0" apply false
}
""")

# 3. App build.gradle.kts
create_file(f"{ROOT}/app/build.gradle.kts", """
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.vexel.pizzaclub"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.vexel.pizzaclub"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_1_8
        targetCompatibility = JavaVersion.VERSION_1_8
    }
    kotlinOptions {
        jvmTarget = "1.8"
    }
    aaptOptions {
        noCompress("tflite") // VERY IMPORTANT FOR TENSORFLOW!
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("com.google.android.material:material:1.11.0")
    implementation("androidx.constraintlayout:constraintlayout:2.1.4")
    
    // TensorFlow Lite
    implementation("org.tensorflow:tensorflow-lite:2.14.0")
    implementation("org.tensorflow:tensorflow-lite-support:0.4.4")
    implementation("org.tensorflow:tensorflow-lite-gpu:2.14.0")

    // OpenCV
    implementation("org.opencv:opencv:4.9.0")
}
""")

# 4. AndroidManifest.xml
create_file(f"{ROOT}/app/src/main/AndroidManifest.xml", """
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.vexel.pizzaclub">

    <!-- Permissions for IP Camera / RTSP -->
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <!-- Permissions for USB Webcams via OTG -->
    <uses-permission android:name="android.permission.CAMERA" />
    <uses-permission android:name="android.permission.USB_PERMISSION" />
    <uses-feature android:name="android.hardware.usb.host" />

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="Pizza OS"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/Theme.AppCompat.Light.NoActionBar">
        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
""")

# 5. MainActivity.kt
create_file(f"{ROOT}/app/src/main/java/com/vexel/pizzaclub/MainActivity.kt", """
package com.vexel.pizzaclub

import android.os.Bundle
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    private lateinit var statusText: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        statusText = findViewById(R.id.statusText)
        
        statusText.text = "Pizza Tracker Engine Loading...\\nReady to initialize OpenCV and TFLite for camera feed."
    }
}
""")

# 6. Basic layout for MainActivity
create_file(f"{ROOT}/app/src/main/res/layout/activity_main.xml", """
<?xml version="1.0" encoding="utf-8"?>
<androidx.constraintlayout.widget.ConstraintLayout 
    xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:background="#1E1E1E">

    <TextView
        android:id="@+id/statusText"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="Initializing Pizza Club OS..."
        android:textColor="#FFFFFF"
        android:textSize="18sp"
        android:textAlignment="center"
        app:layout_constraintBottom_toBottomOf="parent"
        app:layout_constraintEnd_toEndOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintTop_toTopOf="parent" />

</androidx.constraintlayout.widget.ConstraintLayout>
""")

# 7. Create placeholder for Assets (TFLite)
os.makedirs(f"{ROOT}/app/src/main/assets", exist_ok=True)
with open(f"{ROOT}/app/src/main/assets/yolov8n.tflite.txt", "w") as f:
    f.write("REPLACE THIS FILE WITH YOUR EXPORTED yolov8n.tflite FROM GOOGLE COLAB")

print(f"✅ Successfully scaffolded Android project: {os.path.abspath(ROOT)}")
""")
