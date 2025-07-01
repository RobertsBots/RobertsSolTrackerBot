import random
from typing import Optional

def smartcoach_reply(
    wr: float,
    roi: Optional[float] = None,
    tp: Optional[float] = None,
    sl: Optional[float] = None
) -> str:
    try:
        # Sanity-Check und Kategorisierung
        wr = max(0.0, min(1.0, wr or 0.0))
        wr_percent = round(wr * 100, 1)

        category = (
            "high" if wr >= 0.7 else
            "mid" if wr >= 0.5 else
            "low"
        )

        # Dynamische Werte, wenn nicht angegeben
        tp = tp if tp is not None else round(random.uniform(10, 30), 1)
        sl = sl if sl is not None else round(random.uniform(5, 15), 1)
        roi = roi if roi is not None else round(random.uniform(5, 20), 1)

        responses = {
            "high": [
                f"🔥 Bei einer Winrate von {wr_percent}% kannst du fast entspannt zurücklehnen – vergiss aber nicht dein SL bei ca. {sl}% zu setzen. TP-Empfehlung: {tp}%.",
                f"🚀 Diese Wallet rockt mit {wr_percent}%! Für Scalping ideal – SL {sl}%, TP {tp}%, oder einfach Odin feuern lassen!",
                f"📈 {wr_percent}% WR? That's elite. Wenn du den Mut hast: TP {tp}%, SL {sl}%. Oder setz auf Moonbag, ROI liegt bei ~{roi}%.",
                f"🧪 Statistik sagt ja: {wr_percent}% WR = grünes Licht! TP {tp}%, SL {sl}%, aber immer mit Stil.",
                f"🎯 Die Trefferquote liegt bei {wr_percent}% – klare Sache für Copy! Ich würde ein SL von {sl}% nehmen & mit {tp}% TP anpeilen.",
                f"💎 Hohe WR = geringes Risiko. {wr_percent}% ist stark. Überleg dir: Moonbag oder Scalping mit SL {sl}%.",
                f"📊 Die Wallet performt wie ein Uhrwerk: {wr_percent}% WR. TP auf {tp}%, SL auf {sl}%, und ab die Post.",
                f"🧘‍♂️ Zen-Level erreicht: {wr_percent}% WR. Setz dein TP & SL sauber und schau, wie dein Portfolio wächst.",
                f"💹 Mit {wr_percent}% WR ist das ein no-brainer. Aber denk dran: SL {sl}%, TP {tp}% – Risikomanagement bleibt King.",
                f"🔒 Diese Wallet ist solide – {wr_percent}% WR. Ideal für langfristige Moonbags oder auch aggressive Scalps mit SL {sl}%."
            ],
            "mid": [
                f"🤔 {wr_percent}% WR ist so lala – wenn du reingehst, dann SL eng bei {sl}% & TP vorsichtig bei {tp}%.",
                f"🎢 Die Wallet ist eine Achterbahn: {wr_percent}% WR. Überleg dir gut, ob du aufspringst – TP bei {tp}%, SL bei {sl}%.",
                f"🧮 Bei {wr_percent}% WR ist es coin toss. Vielleicht Odin auf 'light mode' spiegeln & eng absichern.",
                f"⚠️ Die Mitte ist gefährlich – {wr_percent}% WR. TP {tp}%, SL {sl}%, oder einfach abwarten & Tee trinken.",
                f"🔍 Solide Performance, aber nicht überragend. {wr_percent}% WR mit ROI ~{roi}%. Für vorsichtige Scalps okay.",
                f"📉 {wr_percent}% WR ist grenzwertig – eventuell manuell mit Beobachtung scalpen.",
                f"🧯 Nicht heiß, nicht kalt – {wr_percent}% WR. Vielleicht als Testballon mit Mini-Position.",
                f"🔁 Mittelklasse-Trader. TP bei {tp}%, SL eng bei {sl}% und Finger am Abzug.",
                f"💼 Semi-professionell unterwegs: {wr_percent}% WR. Könnte laufen, muss aber nicht – TP {tp}%?",
                f"🥶 Diese WR ({wr_percent}%) ist nicht unbedingt warm. Wenn du's wagst: TP {tp}%, SL {sl}%."
            ],
            "low": [
                f"💀 {wr_percent}% WR ist kein gutes Omen – lass lieber die Finger davon, außer du bist extrem risikofreudig.",
                f"📉 Mit {wr_percent}% WR würd ich eher Geld verbrennen – SL bei {sl}%, aber besser gar nicht einsteigen.",
                f"😬 Das sieht nicht gesund aus: {wr_percent}% WR & ROI ~{roi}%. Wenn du's trotzdem wagst: TP klein halten.",
                f"🕳️ Gefahr im Verzug – diese Wallet hat nur {wr_percent}% WR. Vielleicht beim nächsten Signal zuschlagen.",
                f"🐌 Langsamer Tod oder krasser Turnaround? Bei {wr_percent}% WR eher ersteres.",
                f"🧟 {wr_percent}% WR – Totengräber-Trades incoming. Lieber beobachten als mitgehen.",
                f"🔥 Willst du zocken? Dann ist {wr_percent}% WR deine Arena. Ich wär raus.",
                f"❗️Nicht mal Odin würde das kopieren: {wr_percent}% WR. TP irrelevant, SL nützt auch nix.",
                f"🚫 Diese Wallet schreit nach 'nicht folgen'. {wr_percent}% WR? No way.",
                f"💤 Einschläfernde Performance: {wr_percent}% WR. Lass lieber, gibt Besseres."
            ]
        }

        return random.choice(responses[category])

    except Exception as e:
        return f"🤖 SmartCoach konnte leider keine fundierte Antwort geben (Fehler: {e})"
