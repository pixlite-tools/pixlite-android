plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.pixlite.naturalproof"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.pixlite.naturalproof"
        minSdk = 24
        targetSdk = 35
        versionCode = 1
        versionName = "0.1-natural-proof"
    }

    buildTypes {
        debug {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        viewBinding = true
    }

    packaging {
        resources.excludes.add("META-INF/*")
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("com.google.android.material:material:1.12.0")

    implementation("androidx.camera:camera-core:1.5.1")
    implementation("androidx.camera:camera-camera2:1.5.1")
    implementation("androidx.camera:camera-lifecycle:1.5.1")
    implementation("androidx.camera:camera-view:1.5.1")

    implementation("org.opencv:opencv:4.9.0")

    // Document geometry: same ONNX corner detector proved in
    // scanner_geometry_proof/ -- reused, not a new SDK exploration.
    implementation("com.microsoft.onnxruntime:onnxruntime-android:1.29.0")

    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.8.1")
    implementation("androidx.exifinterface:exifinterface:1.3.7")
}
