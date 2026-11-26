import ActivityKit
import AppIntents
import SwiftUI
import WidgetKit

struct BattleLiveActivity: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: BattleAttributes.self) { context in
            // 잠금화면
            BattleSceneView(state: context.state, isStale: context.isStale, spriteSize: 64)
                .padding(14)
                .activityBackgroundTint(.pxNavy)
                .activitySystemActionForegroundColor(.white)
        } dynamicIsland: { context in
            let s = context.state
            return DynamicIsland {
                DynamicIslandExpandedRegion(.leading) {
                    SpriteTimerView(anim: SpriteCatalog.playerBattle, start: s.animStart,
                                    size: 52, mode: s.renderMode)
                }
                DynamicIslandExpandedRegion(.trailing) {
                    SpriteTimerView(anim: s.monster.anim, start: s.animStart,
                                    size: 52, mode: s.renderMode)
                }
                DynamicIslandExpandedRegion(.center) {
                    VStack(spacing: 4) {
                        Text("처치 \(s.kills) · \(s.monster.displayName)").font(.caption.bold())
                        if context.isStale {
                            Text("처치! 갱신을 눌러줘").font(.caption2).foregroundStyle(.yellow)
                        } else {
                            HPBar(start: s.hpBarStart, end: s.deathDate)
                        }
                    }
                }
                DynamicIslandExpandedRegion(.bottom) {
                    HStack {
                        Button(intent: SkillIntent()) { Label("스킬", systemImage: "bolt.fill") }
                            .tint(Color(hex: 0xd6304a))
                        Button(intent: RefreshIntent()) { Label("갱신", systemImage: "arrow.clockwise") }
                            .tint(Color(hex: 0x4a72d8))
                    }
                    .buttonStyle(.borderedProminent)
                    .font(.caption.bold())
                }
            } compactLeading: {
                SpriteTimerView(anim: SpriteCatalog.playerBattle, start: s.animStart,
                                size: 22, mode: s.renderMode)
            } compactTrailing: {
                Text("\(s.kills)").font(.caption.bold().monospacedDigit())
            } minimal: {
                SpriteTimerView(anim: SpriteCatalog.playerBattle, start: s.animStart,
                                size: 20, mode: s.renderMode)
            }
            .keylineTint(Color(hex: 0x2ec4b6))
        }
    }
}
