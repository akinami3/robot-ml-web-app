from pydantic import BaseModel, Field
import yaml
from jinja2 import Template
import json

# ===== デコレーター登録 =====
mqtt_registry = {}

def mqtt_topic(topic_name: str, description: str = "", qos: int = 0, retain: bool = False):
    def decorator(cls):
        mqtt_registry[topic_name] = {
            "model": cls,
            "description": description,
            "qos": qos,
            "retain": retain
        }
        return cls
    return decorator

# ===== ペイロード定義 =====
@mqtt_topic("sensors/temperature", description="温度センサーから送信されるデータ", qos=1)
class TemperaturePayload(BaseModel):
    value: float = Field(..., example=22.5, description="温度値")
    timestamp: str = Field(..., example="2025-11-10T12:00:00Z", description="測定時刻（ISO8601）")

@mqtt_topic("alerts/system", description="システムアラート情報", qos=2, retain=True)
class AlertPayload(BaseModel):
    level: str = Field(..., example="critical", description="アラートレベル")
    message: str = Field(..., example="System overload", description="アラート内容")

# ===== AsyncAPI YAML 生成 =====
def generate_asyncapi_yaml():
    doc = {
        "asyncapi": "2.6.0",
        "info": {"title": "MQTT API", "version": "1.0.0"},
        "servers": {"production": {"url": "mqtt.example.com:1883", "protocol": "mqtt"}},
        "channels": {}
    }
    for topic, info in mqtt_registry.items():
        doc["channels"][topic] = {
            "description": info["description"],
            "subscribe": {
                "message": {
                    "name": info["model"].__name__,
                    "payload": info["model"].schema(),
                    "bindings": {"mqtt": {"qos": info["qos"], "retain": info["retain"]}}
                }
            }
        }
    return doc

# ===== HTML 生成 (AsyncAPI 風) =====
def generate_html(asyncapi_doc, output_file="asyncapi.html"):
    template_str = """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <title>{{ asyncapi.info.title }}</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; background: #f4f4f5; color: #222; }
            header { background: #3e4eb8; color: white; padding: 20px; }
            h1 { margin: 0; font-size: 28px; }
            main { padding: 20px; }
            .channel { background: white; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); padding: 15px; }
            h2 { margin-top: 0; color: #3e4eb8; }
            .label { font-weight: bold; margin-right: 5px; }
            pre { background: #f1f3f5; padding: 10px; border-radius: 5px; overflow-x: auto; }
            .toggle { cursor: pointer; color: #3e4eb8; text-decoration: underline; }
        </style>
        <script>
            function toggle(id) {
                const e = document.getElementById(id);
                if (e.style.display === 'none') e.style.display = 'block';
                else e.style.display = 'none';
            }
        </script>
    </head>
    <body>
        <header>
            <h1>{{ asyncapi.info.title }} - v{{ asyncapi.info.version }}</h1>
        </header>
        <main>
        {% for topic, info in asyncapi.channels.items() %}
            <div class="channel">
                <h2>{{ topic }}</h2>
                <p><span class="label">説明:</span>{{ info.description }}</p>
                <p>
                    <span class="label">QoS:</span>{{ info.subscribe.message.bindings.mqtt.qos }} &nbsp;
                    <span class="label">Retain:</span>{{ info.subscribe.message.bindings.mqtt.retain }}
                </p>
                <p><span class="label">メッセージ名:</span>{{ info.subscribe.message.name }}</p>
                <p><span class="toggle" onclick="toggle('payload-{{ loop.index }}')">ペイロードを表示/非表示</span></p>
                <pre id="payload-{{ loop.index }}" style="display:none">{{ info.subscribe.message.payload | tojson(indent=2) }}</pre>
            </div>
        {% endfor %}
        </main>
    </body>
    </html>
    """
    template = Template(template_str)
    html_output = template.render(asyncapi=asyncapi_doc)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_output)
    print(f"HTML generated: {output_file}")

# ===== 実行 =====
if __name__ == "__main__":
    doc = generate_asyncapi_yaml()
    # YAML も同時生成
    with open("asyncapi.yaml", "w", encoding="utf-8") as f:
        yaml.dump(doc, f, sort_keys=False)
    print("AsyncAPI YAML generated: asyncapi.yaml")

    generate_html(doc)
