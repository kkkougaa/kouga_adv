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
    /// 값이 있으면 그 초만큼 거꾸로 세는 타이머 (한 번만 재생되는 이펙트용)
    var countdown: TimeInterval? = nil
    /// 자르기 방식 (진단용): true = 원래 너비로 그린 뒤 오른쪽 맞춤, false = 칸 너비 안에서 오른쪽 맞춤
    var fixedWidth = true

    private var range: ClosedRange<Date> {
        start...start.addingTimeInterval(countdown ?? 60 * 60 * 24)
    }

    var body: some View {
        ZStack(alignment: .trailing) {
            switch mode {
            case .color:
                digit(font: anim.colorFont, color: .white)
            case .layered, .debug:
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
        Text(timerInterval: range, countsDown: countdown != nil, showsHours: false)
            .font(.custom(font, fixedSize: size))
            .foregroundStyle(color)
            .multilineTextAlignment(.trailing)
            .lineLimit(1)
            .fixedSize(horizontal: fixedWidth, vertical: true)
            .frame(width: size, height: size, alignment: .trailing)
    }
}

/// 몬스터 + 타격 이펙트 + 스킬 폭발. 처치 시각이 지나면(갱신 전) 연기와 동전.
struct MonsterStack: View {
    let state: BattleAttributes.ContentState
    var isStale = false
    let size: CGFloat

    var body: some View {
        ZStack {
            if isStale {
                PixelImage(name: "fx_poof").frame(width: size, height: size)
            } else {
                SpriteTimerView(anim: state.monster.anim, start: state.animStart,
                                size: size, mode: state.renderMode)
                if state.renderMode != .still {
                    SpriteTimerView(anim: SpriteCatalog.fxHit, start: state.animStart,
                                    size: size, mode: state.renderMode)
                    if let at = state.skillAt {
                        SpriteTimerView(anim: SpriteCatalog.fxSkill, start: at,
                                        size: size, mode: state.renderMode, countdown: 3)
                    }
                }
            }
        }
        .frame(width: size, height: size)
    }
}

/// 진단 화면: 그림/글꼴/자르기가 각각 되는지 한 번에 확인
struct DiagnosticsView: View {
    let start: Date
    private let a = SpriteCatalog.playerBattle
    private var range: ClosedRange<Date> { start...start.addingTimeInterval(86400) }

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            HStack(spacing: 6) {
                label("그림")
                PixelImage(name: a.idleFrame).frame(width: 32, height: 32)
                Text(fontStatus).font(.system(size: 10)).lineLimit(2)
                Text(timerInterval: range, countsDown: false, showsHours: false)
                    .font(.system(size: 12).monospacedDigit())
                    .frame(width: 40)
            }
            HStack(spacing: 6) {
                label("컬러")
                Text(timerInterval: range, countsDown: false, showsHours: false)
                    .font(.custom(a.colorFont, fixedSize: 32))
                    .frame(height: 32)
            }
            HStack(spacing: 6) {
                label("겹침")
                ZStack(alignment: .leading) {
                    ForEach(a.layers, id: \.self) { l in
                        Text(timerInterval: range, countsDown: false, showsHours: false)
                            .font(.custom(l.font, fixedSize: 32))
                            .foregroundStyle(Color(hex: l.hex))
                    }
                }
                .frame(height: 32)
            }
            HStack(spacing: 6) {
                label("자름")
                SpriteTimerView(anim: a, start: start, size: 32, mode: .color)
                SpriteTimerView(anim: a, start: start, size: 32, mode: .layered)
                label("B")
                SpriteTimerView(anim: a, start: start, size: 32, mode: .color, fixedWidth: false)
                SpriteTimerView(anim: a, start: start, size: 32, mode: .layered, fixedWidth: false)
            }
        }
        .foregroundStyle(.white)
    }

    private func label(_ t: String) -> some View {
        Text(t).font(.system(size: 10, weight: .bold)).frame(width: 26, alignment: .leading)
    }

    private var fontStatus: String {
        let c = UIFont(name: a.colorFont, size: 10) != nil
        let l = UIFont(name: a.layers.first?.font ?? "", size: 10) != nil
        return "컬러글꼴 \(c ? "있음" : "없음")\n겹침글꼴 \(l ? "있음" : "없음")"
    }
}

/// 잠금화면/앱 미리보기 공용 전투 화면
struct BattleSceneView: View {
    let state: BattleAttributes.ContentState
    var isStale = false
    var spriteSize: CGFloat = 64

    var body: some View {
        if state.renderMode == .debug {
            DiagnosticsView(start: state.animStart)
        } else {
            scene
        }
    }

    private var scene: some View {
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
                MonsterStack(state: state, isStale: isStale, size: spriteSize)
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
