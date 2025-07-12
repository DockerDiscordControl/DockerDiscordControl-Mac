# Container Timeout Configuration

Diese Dokumentation erklärt das flexible Container-Timeout-System von DockerDiscordControl, das entwickelt wurde, um Performance-Probleme bei verschiedenen Container-Typen zu lösen.

## Überblick

Das System verwendet pattern-basierte Timeout-Konfiguration anstelle von hardcodierten Container-Namen. Dies ermöglicht maximale Flexibilität und einfache Wartung.

## Standard-Timeout-Konfiguration

### Environment Variables
```bash
# Schnelle Timeouts (für Game-Server Stats)
DDC_FAST_STATS_TIMEOUT=2.0
DDC_FAST_INFO_TIMEOUT=2.0

# Langsame Timeouts (für Standard-Container)
DDC_SLOW_STATS_TIMEOUT=3.0
DDC_SLOW_INFO_TIMEOUT=3.0
```

### Eingebaute Container-Typen

#### Game Server (Fast Stats, Slow Info)
- **Patterns**: minecraft, factorio, terraria, starbound, rust, ark, palworld, satisfactory, valheim, v-rising, conan, dayz, csgo, tf2, gmod, arma, squad, etc.
- **Stats Timeout**: 2.0s (schnell, um Blockierung zu vermeiden)
- **Info Timeout**: 3.0s (langsam, für detaillierte Informationen)

#### Media Server (Slow Stats, Fast Info)
- **Patterns**: plex, jellyfin, emby, kodi, sonarr, radarr, transmission, qbittorrent, etc.
- **Stats Timeout**: 3.0s
- **Info Timeout**: 2.0s

#### Database (Slow Stats, Fast Info)
- **Patterns**: mysql, mariadb, postgres, mongodb, redis, elasticsearch, etc.
- **Stats Timeout**: 3.0s
- **Info Timeout**: 2.0s

#### Web Server (Slow Stats, Fast Info)
- **Patterns**: nginx, apache, caddy, traefik, nodejs, php, wordpress, nextcloud, etc.
- **Stats Timeout**: 3.0s
- **Info Timeout**: 2.0s

## Benutzerdefinierte Konfiguration

### Konfigurationsdatei erstellen
```bash
cp config/container_timeouts.json.example config/container_timeouts.json
```

### Beispiel-Konfiguration
```json
{
  "description": "Benutzerdefinierte Container-Timeout-Konfiguration",
  "environment_variables": {
    "DDC_FAST_STATS_TIMEOUT": "1.5",
    "DDC_SLOW_STATS_TIMEOUT": "4.0",
    "DDC_FAST_INFO_TIMEOUT": "2.0",
    "DDC_SLOW_INFO_TIMEOUT": "3.5"
  },
  "custom_patterns": {
    "meine_game_server": {
      "patterns": ["mein-minecraft", "mein-server"],
      "stats_timeout": 1.0,
      "info_timeout": 2.0
    },
    "langsame_services": {
      "patterns": ["heavy-database", "big-app"],
      "stats_timeout": 8.0,
      "info_timeout": 6.0
    }
  },
  "container_overrides": {
    "genauer-container-name": {
      "stats_timeout": 0.5,
      "info_timeout": 1.0
    }
  }
}
```

## Prioritäten-System

Das System verwendet folgende Prioritäten (höchste zuerst):

1. **Container Overrides** - Exakte Container-Namen
2. **Custom Patterns** - Benutzerdefinierte Patterns
3. **Built-in Patterns** - Eingebaute Container-Typ-Patterns
4. **Default** - Standard-Timeout-Konfiguration

## Debugging

### Container-Typ-Informationen abrufen
```python
from utils.docker_utils import get_container_type_info

# Beispiel für Debugging
info = get_container_type_info("mein-satisfactory-server")
print(f"Type: {info['type']}")
print(f"Matched Pattern: {info['matched_pattern']}")
print(f"Timeouts: {info['timeout_config']}")
print(f"Config Source: {info['config_source']}")
```

### Performance-Test ausführen
```python
from utils.docker_utils import test_docker_performance

# Teste alle Container
results = await test_docker_performance()

# Teste spezifische Container
results = await test_docker_performance(
    container_names=["satisfactory", "valheim", "plex"],
    iterations=3
)
```

## Logs überwachen

```bash
# Timeout-Konfiguration überwachen
docker logs ddc | grep "Container.*matches.*pattern"

# Stats-Timeouts überwachen
docker logs ddc | grep "Stats timeout"

# Performance-Logs überwachen
docker logs ddc | grep "edit_single_message"
```

## Beispiele

### Für Game-Server optimieren
```json
{
  "custom_patterns": {
    "ultra_fast_games": {
      "patterns": ["minecraft", "terraria", "starbound"],
      "stats_timeout": 1.0,
      "info_timeout": 1.5
    }
  }
}
```

### Für langsame Container
```json
{
  "custom_patterns": {
    "slow_containers": {
      "patterns": ["big-database", "heavy-processing"],
      "stats_timeout": 10.0,
      "info_timeout": 8.0
    }
  }
}
```

### Für spezifische Container
```json
{
  "container_overrides": {
    "problematic-container": {
      "stats_timeout": 0.5,
      "info_timeout": 1.0
    },
    "very-slow-container": {
      "stats_timeout": 15.0,
      "info_timeout": 10.0
    }
  }
}
```

## Troubleshooting

### Häufige Probleme

1. **Container wird nicht erkannt**
   - Überprüfen Sie die Logs nach "matches.*pattern"
   - Fügen Sie ein custom_pattern hinzu

2. **Timeouts zu kurz**
   - Erhöhen Sie die Timeout-Werte in der Konfiguration
   - Verwenden Sie container_overrides für spezifische Container

3. **Performance noch langsam**
   - Überprüfen Sie die Docker-System-Performance
   - Verwenden Sie den Performance-Test zur Diagnose

### Konfiguration neu laden
```bash
# Bot neu starten um Konfiguration zu laden
docker restart ddc
```

## Best Practices

1. **Beginnen Sie mit den Standard-Timeouts** und passen Sie nur bei Bedarf an
2. **Verwenden Sie Environment Variables** für globale Änderungen
3. **Nutzen Sie custom_patterns** für Gruppen ähnlicher Container
4. **Verwenden Sie container_overrides** nur für spezielle Fälle
5. **Testen Sie Änderungen** mit der Performance-Test-Funktion
6. **Überwachen Sie die Logs** nach Änderungen

## Migration von alten Versionen

Wenn Sie von einer älteren Version mit hardcodierten Container-Namen upgraden:

1. Ihre bestehenden Container funktionieren automatisch mit den neuen Pattern-basierten Timeouts
2. Die Performance sollte sich sofort verbessern
3. Bei Bedarf können Sie spezifische Anpassungen in der Konfigurationsdatei vornehmen 