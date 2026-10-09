# LIPSYNC_FEASIBILITY — lip-sync RU-озвучки на локальном железе (0₽)

Дата: 29.09.2026. Задача: kanban t_ad96a15d (video-editor). Тип: research. В пайплайн НЕ внедрено — отдельное решение владельца.

## ВЕРДИКТ

НЕВОЗМОЖНО в связке «0₽ + пермиссивная лицензия под коммерцию + текущее железо».
- Единственный инструмент, реально работающий на этом CPU-only железе (Wav2Lip), юридически закрыт для коммерческого использования (non-commercial, веса на датасете LRS2/BBC).
- Коммерчески-пермиссивные инструменты (LatentSync — Apache-2.0, MuseTalk — MIT) требуют NVIDIA CUDA GPU; на этой машине его нет (Intel Arc iGPU, CUDA отсутствует).
- Технически-демонстрационный прогон Wav2Lip возможен (см. «Демо» ниже — не завершён из-за недоступности весов детектора s3fd в проверенных зеркалах и исчерпания бюджета вызовов), но вердикт не меняет: результат нельзя публиковать в коммерческом контенте.

## ЖЕЛЕЗО (проверено фактически, не угадано)

Команда: `powershell.exe Get-CimInstance Win32_VideoController / Win32_Processor / Win32_ComputerSystem`, exit 0:
- CPU: Intel Core Ultra 5 125H, 14 ядер.
- RAM: 15.5 GB.
- GPU: Intel(R) Arc(TM) Graphics (встроенная iGPU Meteor Lake), драйвер 32.0.101.6078, AdapterRAM 2 GB. NVIDIA/CUDA нет: `nvidia-smi` — command not found, `C:\Program Files\NVIDIA Corporation` — отсутствует.
- Диск C:: 32 GB свободно (90% занято) — `df -h /c`.
- Окружение: `C:/Users/max/Desktop/all/video/.venv`, Python 3.11.9, torch 2.8.0+cpu (то же, на котором собирался RU-дубль V7 XTTS-v2), librosa 0.11.0, numba 0.67.0, numpy 1.26.4; opencv-python доустановлен в рамках задачи.

## ИНСТРУМЕНТЫ

| Инструмент | Лицензия (коммерция) | Железо | На этой машине | Итог |
|---|---|---|---|---|
| Wav2Lip (Rudrabha/Wav2Lip) | Non-commercial open-source version; авторы запрещают коммерцию (веса обучены на LRS2); лицензия менялась с MIT на non-commercial (issues #104, #623) | Работает на CPU (медленно) | Технически да | ЗАПРЕЩЁН лицензией для нашего контента |
| LatentSync 1.5/1.6 (bytedance/LatentSync) | Apache-2.0 (код и веса) — коммерчески свободен | Требуется CUDA GPU (диффузионная модель; ~20 GB VRAM stage2-train, инференс существенно GPU-зависим) | Нет CUDA; на CPU — дни на минуту видео; порт на Intel XPU/IPEX официально не поддержан | НЕВОЗМОЖНО на текущем железе |
| SadTalker (OpenTalker) | Код Apache-2.0, но LICENSE оговаривает third-party компоненты; сторонние обзоры отмечают non-commercial модели | CUDA GPU | Нет CUDA; и главное — это генерация talking-head из СТАТИЧНОГО фото, а не lip-sync существующего видео | НЕ ПОД ЗАДАЧУ |
| MuseTalk (TMElyralab) | MIT (код) | NVIDIA CUDA для real-time | Нет CUDA | НЕВОЗМОЖНО на текущем железе |

## СТОИМОСТЬ И ВРЕМЯ (на минуту готового видео)

- Деньги: 0₽ во всех вариантах (локальный инференс; электричество не учитываем).
- Wav2Lip на этом CPU: ОЦЕНКА (не замерено — демо не завершено): детекция лиц s3fd ~1–3 с/кадр + генератор; при 30 fps порядок 30–90 минут на 1 минуту видео. Для сравнения: на CUDA GPU Wav2Lip ~1–2 мин/мин, LatentSync ~5–15 мин/мин (RTX 3060-класс).
- Качество Wav2Lip на вертикали 9:16: рот генерируется в 96×96 и апскейлится — на крупном плане 1080×1920 (наш материал V7 — говорящая голова крупно) это заметное мыло/артефакты вокруг рта; для talking-head крупного плана качество ниже приемлемого порога платформы даже при работающем железе.

## ДЕМО (попытка, не завершена)

Материал: V7 NG-V7-01_final.mp4 (1080×1920, 30 fps, 24.6 с, RU-дубль XTTS-v2 уже в миксе). Кадр на t=3c проверен визуально: мужчина крупным планом, фронтально, рот виден — материал пригоден для lip-sync-демо.
Шаги (workspace t_ad96a15d):
- Клонирован Rudrabha/Wav2Lip (git clone --depth 1).
- Скачан checkpoints/wav2lip.pth: 435 807 851 байт, SHA256 b78b681b68ad9fe6c6fb1debc6ff43ad05834a8af8a62ffc4167b7b34ef63c37 (зеркало HF rippertnt/wav2lip; официальный линк README — SharePoint).
- Веса детектора лица s3fd-619bc30812.pth получить НЕ удалось: adrianbulat.com — 404 (линк мёртв), jjbruh/face — 401, camenduru/Wav2Lip, numz/wav2lip_studio, rippertnt (путь face_detection/...), MonsterMMORPG/tools — 404. Найдены кандидаты через HF API: `irishavmishra/s3fd-face-detector`, `n0x1103/s3fd` — не проверены (бюджет вызовов карты исчерпан).
- Инференс не запускался → замер времени и визуальная оценка качества на нашем материале ОТСУТСТВУЮТ; цифры в разделе «Время» помечены как оценка.
Папка C:/Users/max/Documents/video-quality-upgrade/V7/lipsync_demo/ НЕ создавалась — демо-файла нет.

## РЕКОМЕНДАЦИЯ

1. В пайплайн не внедрять; в provenance роликов lip-sync не заявлять.
2. Текущий подход V7 (RU-дубль XTTS-v2 + полные субтитры) остаётся основным: субтитры маскируют расхождение артикуляции, это стандартная практика локализации.
3. Если владелец захочет lip-sync в будущем, минимальные требования: NVIDIA GPU с CUDA (от 8–12 GB VRAM для LatentSync-инференса) + LatentSync (Apache-2.0, 0₽). Wav2Lip не использовать для публикуемого контента ни при каком железе (лицензия).
4. Демонстрационный (непубличный) прогон Wav2Lip на CPU можно добить отдельной картой: докачать s3fd из найденных HF-репозиториев, прогнать 5–10 с с --nosmooth; ожидаемая длительность — десятки минут, качество — «мыльный рот» на крупном плане.

## EVIDENCE-ИНДЕКС

- Железо: вывод Get-CimInstance (в тексте); nvidia-smi — command not found; df -h /c — 32G avail.
- Лицензии: github.com/Rudrabha/Wav2Lip (README «Non Commercial Open-source Version»; issues #104, #623), github.com/bytedance/LatentSync (LICENSE Apache-2.0), github.com/OpenTalker/SadTalker (LICENSE Apache-2.0 + third-party оговорка), sync.so/blog/what-is-latentsync (Apache-2.0, коммерчески свободен).
- Веса: wav2lip.pth SHA256 b78b681b... (см. выше); HTTP-коды зеркал s3fd: 404/401 (лог в разделе «Демо»).
- Материал V7: ffprobe NG-V7-01_final.mp4 — 1080×1920, 30/1 fps, 24.600 с; кадр frame_probe.png (t=3c) — лицо крупным планом, фронтально.
