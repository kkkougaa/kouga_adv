import AppIntents
import SwiftUI
import UIKit

extension Color {
    init(hex: UInt32) {
        self.init(.sRGB,
                  red: Double((hex >> 16) & 0xff) / 255,
                  green: Double((hex >> 8) & 0xff) / 255,
                  blue: Double(hex & 0xff) / 255)
    }

    static let pxNavy = Color(hex: 0x1b1f3b)
    static let pxPanel = Color(hex: 0x2a2f55)
}

/// 도트 그림 한 장 (번들의 png)
struct PixelImage: View {
    let name: String
    var body: some View {
        if let img = UIImage(named: name) {
            Image(uiImage: img).resizable().interpolation(.none).aspectRatio(contentMode: .fit)
        } else {
            Color.clear
        }
    }
}

/// ★ 글꼴 꼼수 애니메이션
/// 시스템 타이머 글자(0:07 처럼 표시)를 숫자=프레임 글꼴로 그리고,
/// 맨 오른쪽 한 글자(초의 일의 자리)만 보이게 잘라낸다 → 갱신 없이 초당 1프레임.
struct SpriteTimerView: View {
    let anim: SpriteAnim
    let start: Date
    let size: CGFloat
    var mode: SpriteRenderMode = .color
    var flipped = false

    var body: some View {
        ZStack(alignment: .trailing) {
            switch mode {
            case .color:
                digit(font: anim.colorFont, color: .white)
            case .layered:
                ForEach(anim.layers, id: \.self) { layer in
                    digit(font: layer.font, color: Color(hex: layer.hex))
                }
            case .still:
                PixelImage(name: anim.idleFrame).frame(width: size, height: size)
            }
        }
        .frame(width: size, height: size, alignment: .trailing)
        .clipped()
        .scaleEffect(x: flipped ? -1 : 1, y: 1)
    }

    private func digit(font: String, color: Color) -> some View {
        Text(timerInterval: start...start.addingTimeInterval(60 * 60 * 24),
             countsDown: false, showsHours: false)
            .font(.custom(font, fixedSize: size))
            .foregroundStyle(color)
            .multilineTextAlignment(.trailing)
            .lineLimit(1)
            .fixedSize()
            .frame(width: size, height: size, alignment: .trailing)
    }
}

/// 잠금화면/앱 미리보기 공용 전투 화면
struct BattleSceneView: View {
    let state: BattleAttributes.ContentState
    var isStale = false
    var spriteSize: CGFloat = 64

    var body: some View {
        VStack(spacing: 8) {
            HStack {
                Text("처치 \(state.kills)").font(.headline.monospacedDigit())
                Spacer()
                Text("\(state.gold) G").font(.subheadline.monospacedDigit()).foregroundStyle(Color(hex: 0xf2d040))
            }
            HStack(alignment: .bottom, spacing: 8) {
                SpriteTimerView(anim: SpriteCatalog.playerBattle, start: state.animStart,
                                size: spriteSize, mode: state.renderMode)
                VStack(alignment: .leading, spacing: 4) {
                    Text("\(state.monsterIndex + 1). \(state.monster.displayName)")
                        .font(.caption.bold())
                    if isStale {
                        Text("처치! 갱신을 눌러줘").font(.caption2).foregroundStyle(.yellow)
                    } else {
                        HPBar(start: state.hpBarStart, end: state.deathDate)
                    }
                }
                .frame(maxWidth: .infinity)
                SpriteTimerView(anim: state.monster.anim, start: state.animStart,
                                size: spriteSize, mode: state.renderMode)
            }
            HStack(spacing: 8) {
                Button(intent: SkillIntent()) {
                    Label("스킬", systemImage: "bolt.fill").frame(maxWidth: .infinity)
                }
                .tint(Color(hex: 0xd6304a))
                Button(intent: RefreshIntent()) {
                    Label("갱신", systemImage: "arrow.clockwise").frame(maxWidth: .infinity)
                }
                .tint(Color(hex: 0x4a72d8))
            }
            .buttonStyle(.borderedProminent)
            .font(.caption.bold())
        }
        .foregroundStyle(.white)
    }
}

/// 타이머 진행 막대 = 몬스터 체력바 (갱신 없이 줄어듦)
struct HPBar: View {
    let start: Date
    let end: Date
    var body: some View {
        ProgressView(timerInterval: start...max(end, start.addingTimeInterval(0.1)), countsDown: true) {
            EmptyView()
        } currentValueLabel: {
            EmptyView()
        }
        .progressViewStyle(.linear)
        .tint(Color(hex: 0xd6304a))
    }
}
