import ActivityKit
import SwiftUI

struct ContentView: View {
    @EnvironmentObject var game: BattleController
    @Environment(\.scenePhase) private var scenePhase
    @State private var testStart = Date.now
    private let ticker = Timer.publish(every: 1, on: .main, in: .common).autoconnect()

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    walletCard
                    previewCard
                    battleButtons
                    upgradeCard
                    renderModeCard
                    spriteGallery
                    if let msg = game.lastMessage {
                        Text(msg).font(.footnote).foregroundStyle(.secondary)
                    }
                }
                .padding()
            }
            .background(Color.pxNavy.ignoresSafeArea())
            .navigationTitle("도트 전사")
        }
        .onReceive(ticker) { _ in
            // 앱이 켜져 있는 동안엔 몬스터가 바뀔 때마다 라이브 액티비티 갱신
            Task { await game.pushUpdate() }
        }
        .onChange(of: scenePhase) { _, phase in
            if phase == .active {
                game.reload()
                Task { await game.pushUpdate(force: true) }
            }
        }
    }

    private var walletCard: some View {
        HStack {
            VStack(alignment: .leading) {
                Text("골드").font(.caption).foregroundStyle(.secondary)
                Text("\(game.totalGold) G").font(.title2.bold().monospacedDigit())
                    .foregroundStyle(Color(hex: 0xf2d040))
            }
            Spacer()
            VStack(alignment: .trailing) {
                Text("공격력").font(.caption).foregroundStyle(.secondary)
                Text("Lv.\(game.state.stats.attackLevel) (\(game.state.stats.attack))")
                    .font(.title3.bold().monospacedDigit())
            }
        }
        .card()
    }

    @ViewBuilder private var previewCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("전투 미리보기 (잠금화면과 같은 화면)").font(.caption).foregroundStyle(.secondary)
            if let cs = game.contentState() {
                BattleSceneView(state: cs, isStale: cs.deathDate < .now)
            } else {
                HStack {
                    PixelImage(name: SpriteCatalog.playerBattle.idleFrame).frame(width: 64, height: 64)
                    Text("전투 대기 중").foregroundStyle(.secondary)
                    Spacer()
                }
            }
        }
        .card()
    }

    private var battleButtons: some View {
        HStack {
            Button {
                Task { await game.startBattle() }
            } label: {
                Label(game.state.segment == nil ? "전투 시작" : "다시 띄우기", systemImage: "play.fill")
                    .frame(maxWidth: .infinity)
            }
            .tint(Color(hex: 0x2ec4b6))
            Button {
                Task { await game.stopBattle() }
            } label: {
                Label("종료·정산", systemImage: "stop.fill").frame(maxWidth: .infinity)
            }
            .tint(Color(hex: 0x6b3a24))
            .disabled(game.state.segment == nil)
        }
        .buttonStyle(.borderedProminent)
        .controlSize(.large)
    }

    private var upgradeCard: some View {
        HStack {
            VStack(alignment: .leading) {
                Text("무기 강화").font(.headline)
                Text("공격력 +2 · 비용 \(game.state.stats.upgradeCost) G")
                    .font(.caption).foregroundStyle(.secondary)
            }
            Spacer()
            Button("강화") { Task { await game.upgradeAttack() } }
                .buttonStyle(.borderedProminent)
                .tint(Color(hex: 0xd6304a))
        }
        .card()
    }

    private var renderModeCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("애니메이션 방식 시험").font(.headline)
            Picker("방식", selection: Binding(
                get: { game.state.renderMode },
                set: { m in Task { await game.setRenderMode(m) } })) {
                ForEach(SpriteRenderMode.allCases, id: \.self) { Text($0.label).tag($0) }
            }
            .pickerStyle(.segmented)
            HStack(spacing: 12) {
                ForEach(SpriteRenderMode.allCases, id: \.self) { m in
                    VStack {
                        SpriteTimerView(anim: SpriteCatalog.playerBattle, start: testStart,
                                        size: 56, mode: m)
                        Text(m.label).font(.caption2).foregroundStyle(.secondary)
                    }
                }
            }
            HStack(spacing: 4) {
                Text("기준 타이머:").foregroundStyle(.secondary)
                Text(timerInterval: testStart...testStart.addingTimeInterval(86400),
                     countsDown: false, showsHours: false)
                    .monospacedDigit()
            }
            .font(.caption2)
        }
        .card()
    }

    private var spriteGallery: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("도트 목록").font(.headline)
            ScrollView(.horizontal, showsIndicators: false) {
                HStack {
                    ForEach([SpriteCatalog.playerBattle] + MonsterKind.allCases.map(\.anim), id: \.self) { a in
                        PixelImage(name: a.idleFrame).frame(width: 48, height: 48)
                    }
                }
            }
        }
        .card()
    }
}

private extension View {
    func card() -> some View {
        self.padding()
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color.pxPanel, in: RoundedRectangle(cornerRadius: 14))
    }
}
