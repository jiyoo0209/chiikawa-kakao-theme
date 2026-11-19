import com.android.build.gradle.internal.dsl.BaseAppModuleExtension
import java.util.Properties

// 테마 이름·패키지 ID는 theme.properties 에서 읽음
val themeProps = Properties().apply {
    rootProject.file("theme.properties").reader(Charsets.UTF_8).use { load(it) }
}
val themePackageId: String = themeProps.getProperty("packageId", "mytheme").trim()
// GitHub Actions 에서 빌드 번호를 넘겨주면 그 값으로 버전 코드를 올림 (덮어쓰기 설치 가능)
val buildNumber: Int = (findProperty("buildNumber") as String?)?.toIntOrNull() ?: 1

buildscript {
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath("com.android.tools.build:gradle:8.7.2")
        classpath("org.jetbrains.kotlin:kotlin-gradle-plugin:1.9.25")
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
    }

    apply(plugin = "com.android.application")
    apply(plugin = "kotlin-android")

    plugins.withId("com.android.application") {
        extensions.configure<BaseAppModuleExtension> {
            namespace = "com.kakao.talk.theme.apeach"

            compileSdk = 35
            buildToolsVersion = "35.0.0"

            defaultConfig {
                minSdk = 28
                targetSdk = 35

                versionName = "1.0.$buildNumber"
                versionCode = 100 + buildNumber
                applicationId = "com.kakao.talk.theme.$themePackageId"

                sourceSets {
                    getByName("main") {
                        res.srcDirs("src/main/theme", "src/main/theme-adv")
                    }
                }
            }

            signingConfigs {
                create("theme") {
                    storeFile = rootProject.file("keystore/theme.jks")
                    storePassword = "kakaotheme"
                    keyAlias = "theme"
                    keyPassword = "kakaotheme"
                }
            }

            buildTypes {
                getByName("release") {
                    isMinifyEnabled = false
                    signingConfig = signingConfigs.getByName("theme")
                }
            }

            compileOptions {
                sourceCompatibility = JavaVersion.VERSION_21
                targetCompatibility = JavaVersion.VERSION_21
            }

            buildFeatures {
                viewBinding = true
            }

            dependencies.add("implementation", "org.jetbrains.kotlin:kotlin-stdlib-jdk8:1.9.25")
            dependencies.add("implementation", "androidx.annotation:annotation:1.9.1")
        }
    }
}
