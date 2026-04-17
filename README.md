# SawmeCrypto — Transparent Key Exchange Visualizer

## Folder Structure
```
SawmeCrypto/
├── app.py                    ← Main GUI (run this)
├── common/
│   ├── __init__.py
│   ├── Extra.py              ← Timestamp ping utilities
│   ├── XORSHIFT.py           ← XorShift32 PRNG + Beta generator
│   ├── Divisor_utils.py      ← Divisor counting + FdivisorMixer
│   ├── Prime_Utils.py        ← PrimeFun (next prime after XOR)
│   └── sawme_cipher.py       ← Sawme Feistel cipher (encrypt/decrypt)
└── protocols/
    ├── __init__.py
    └── engine.py             ← Alice (server) + Bob (client) threads
```

## Run
```bash
pip install pycryptodome
python app.py
```

## What You'll See
- **Left panel (Alice / Server)** — her live cryptographic values
- **Right panel (Bob / Client)** — his live cryptographic values
- **Center Timeline** — every protocol step as it happens
- **Key Inspector tab** — full verbose dump of all values exchanged
- **Secure Chat tab** — type messages; encrypted with Sawme cipher using the shared key

## Protocol Summary
1. Bob sends a time-stamp ping → Alice verifies
2. Both generate: secret (a/b), generator (genA/genB), public param (PA/PB)
3. Bob sends `Combine1 = genA^genB^PA` and `PA` — hides genA
4. Alice sends `Combine2 = Combine1^PB` — hides PB
5. Both exchange divisor counts (La, Lb) → compute Lembda
6. Both derive same `prime = next_prime(PA^PB)`
7. Both compute `pow(genA*genB*Lembda, secret, prime) ^ Beta`
8. Both XOR received value with Beta to get peer's session value
9. Shared key = `pow(peer_session_val, own_secret, prime)`
10. Sawme cipher key derived from shared key hex
