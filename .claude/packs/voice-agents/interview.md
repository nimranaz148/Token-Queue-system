# Voice agents — technical interview

Ask only what changes the build. Each question carries a recommendation and a free-tier default; the user answers yes or names a change.

## Q1. Phone, web, or both?

- **Recommend:** Decide the channel first: phone needs a telephony provider and number; web needs only WebRTC.
- **Free default:** Provider trial credit while prototyping.

## Q2. Speech pipeline: one real-time speech model, or separate speech-to-text, language model and text-to-speech?

- **Recommend:** A real-time speech API for the lowest latency; separate parts when you need control over each or a specific voice.
- **Free default:** Per-minute pricing: set a cost cap before testing.

## Q3. What is the latency target?

- **Recommend:** Under about one second from the caller finishing to the agent starting; measure it per turn.
- **Free default:** None needed.

## Q4. How are interruptions handled?

- **Recommend:** Barge-in must stop the agent speaking within a fraction of a second.
- **Free default:** None needed.

## Q5. Languages, accents and noise?

- **Recommend:** List them; test with real recordings of each, not studio audio.
- **Free default:** None needed.

## Q6. When does a human take over?

- **Recommend:** Define the handoff triggers (frustration, repeated failure, sensitive topic, explicit request) and the handoff channel.
- **Free default:** None needed.

## Q7. Recording, consent and retention?

- **Recommend:** Announce recording where the law requires it; store transcripts only as long as needed; redact personal data.
- **Free default:** None needed.

