from pathlib import Path
import re, json, sys

root = Path(sys.argv[1])

# ArrangerConsoleScreen: remove non-functional MIC VOL control and fix compile-time type.
p = root / "app/src/main/java/com/example/ui/ArrangerConsoleScreen.kt"
s = p.read_text()
s = s.replace('    val micVolume by viewModel.micVolume.collectAsStateWithLifecycle()\n', '')
s = s.replace('            micVolume = micVolume,\n', '')
s = s.replace('            onMicVolumeChange = { viewModel.setMicVolume(it) },\n', '')
s = s.replace('    micVolume: Float,\n', '')
s = s.replace('    onMicVolumeChange: (Float) -> Unit,\n', '')
s = re.sub(r'\n\s*RotaryKnob\(\s*label = "MIC VOL",\s*value = micVolume,\s*onValueChange = onMicVolumeChange,\s*ledColor = ConsoleColors\.LedGreen,\s*size = 36\.dp\s*\)\s*', '\\n', s)
s = s.replace('    chordDetectMode: ChordDetectMode,', '    chordDetectMode: String,')
p.write_text(s)

# Chord detector: deterministic two-note handling + truthful unknown result.
p = root / "app/src/main/java/com/example/model/ChordDetector.kt"
s = p.read_text()
s = s.replace('    FIFTH("5", listOf(0, 7))\n',
              '    FIFTH("5", listOf(0, 7)),\n    UNKNOWN("?", listOf(0))\n')
s = s.replace('            val list = pitchClasses.toList()\n', '            val list = pitchClasses.sorted()\n')
s = s.replace('        // Fallback: root is lowest note, major triad\n        return ChordInfo(bassNote, ChordType.MAJOR, bassNote)\n',
              '        // Do not invent a major chord for an unrecognized note set.\n        return ChordInfo(bassNote, ChordType.UNKNOWN, bassNote)\n')
p.write_text(s)

# Truthful diagnostics.
p = root / "app/src/main/java/com/example/ui/screens/SettingsDisplayScreen.kt"
s = p.read_text()
s = s.replace('DiagRow("POLYPHONY", "32 Dynamic Voices + 8 Drums")',
              'DiagRow("POLYPHONY", "32 Voice Synthesis Pool")')
s = s.replace('text = "● ENGINE VERIFIED: 100% OPERATIONAL",',
              'text = "● LOCAL AUDIO ENGINE",')
p.write_text(s)

# Remove unused AI Studio/Firebase build hooks and custom signing.
p = root / "app/build.gradle.kts"
s = p.read_text()
s = s.replace('import com.google.gms.googleservices.GoogleServicesPlugin.MissingGoogleServicesStrategy\n\n', '')
s = s.replace('  alias(libs.plugins.secrets)\n', '')
s = s.replace('  alias(libs.plugins.google.services)\n', '')
start = s.find('  signingConfigs {')
if start != -1:
    end = s.find('\n  buildTypes {', start)
    if end == -1:
        raise RuntimeError('buildTypes block not found')
    s = s[:start] + s[end:]
s = s.replace('      signingConfig = signingConfigs.getByName("release")\n', '')
s = s.replace('    debug { signingConfig = signingConfigs.getByName("debugConfig") }\n', '')
start = s.find('// Configure the Secrets Gradle Plugin')
if start != -1:
    end = s.find('dependencies {', start)
    if end == -1:
        raise RuntimeError('dependencies block not found')
    s = s[:start] + s[end:]
for line in [
    '  implementation(platform(libs.firebase.bom))\n',
    '  implementation(libs.firebase.ai)\n',
    '  implementation(libs.firebase.appcheck.recaptcha)\n',
    '  implementation(libs.firebase.appcheck.debug)\n'
]:
    s = s.replace(line, '')
p.write_text(s)

p = root / "build.gradle.kts"
s = p.read_text()
s = s.replace('  alias(libs.plugins.secrets) apply false\n', '')
s = s.replace('  alias(libs.plugins.google.services) apply false\n', '')
p.write_text(s)

p = root / "gradle/libs.versions.toml"
s = p.read_text()
for line in [
    'firebaseBom = "34.17.0"\n',
    'secretsGradlePlugin = "2.0.1"\n',
    'googleServices = "4.5.0"\n',
    'firebase-bom = { group = "com.google.firebase", name = "firebase-bom", version.ref = "firebaseBom" }\n',
    'firebase-ai = { group = "com.google.firebase", name = "firebase-ai" }\n',
    'firebase-appcheck-recaptcha = { group = "com.google.firebase", name = "firebase-appcheck-recaptcha" }\n',
    'firebase-appcheck-debug = { group = "com.google.firebase", name = "firebase-appcheck-debug" }\n',
    'firebase-firestore = { group = "com.google.firebase", name = "firebase-firestore" }\n',
    'firebase-auth = { group = "com.google.firebase", name = "firebase-auth" }\n',
    'secrets = { id = "com.google.android.libraries.mapsplatform.secrets-gradle-plugin", version.ref = "secretsGradlePlugin" }\n',
    'google-services = { id = "com.google.gms.google-services", version.ref = "googleServices" }\n'
]:
    s = s.replace(line, '')
p.write_text(s)

p = root / "gradle.properties"
s = p.read_text().replace('# Allow the google-services plugin to work even if the google-services.json is not present.\n', '')
p.write_text(s)

(root / ".env.example").write_text('# No API keys are required by the current local audio engine.\n')
(root / "README.md").write_text('# Biruk Arranger\n\nNative Android arranger keyboard with local procedural audio synthesis.\n\nThe current build does not require Gemini, Firebase, or an external API key.\n')

# Metadata no longer claims a server-side Gemini capability.
p = root / "metadata.json"
data = json.loads(p.read_text())
data["description"] = "Native Android arranger keyboard with local procedural audio synthesis, automatic accompaniment styles, learning content, registrations, mixer and effects."
data.pop("majorCapabilities", None)
p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
