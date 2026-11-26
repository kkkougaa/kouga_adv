import ActivityKit
import Foundation

/// 게임 상태 + 라이브 액티비티 관리. 앱 화면과 라이브 액티비티 버튼(앱 인텐트) 둘 다 이걸 쓴다.
@MainActor
final class BattleController: ObservableObject {
    static let shared = BattleController()

    @Published private(set) var state: GameState
    @Published var lastMessage: String?
    private var lastPushedIndex: Int?

    private init() { state = GameStore.load() }

    // MARK: 계산값

    func status(at now: Date = .now) -> BattleStatus? {
        state.segment.map { BattleEngine.status($0, at: now) }
    }

    var totalGold: Int { state.bankedGold + (status()?.gold ?? 0) }

    var currentActivity: Activity<BattleAttributes>? { Activity<BattleAttributes>.activities.first }

    func contentState(at now: Date = .now) -> BattleAttributes.ContentState? {
        guard let seg = state.segment else { return nil }
        return .init(status: BattleEngine.status(seg, at: now), segment: seg, mode: state.renderMode)
    }

    // MARK: 행동

    func startBattle() async {
        reload()
        let now = Date.now
        if state.segment == nil {
            state.segment = BattleEngine.newBattle(at: now, stats: state.stats)
        } else {
            // 이어서 하되 애니메이션 기준을 지금으로 맞춤
            state.segment = BattleEngine.rebase(state.segment!, at: now, attack: state.stats.attack)
        }
        save()
        for a in Activity<BattleAttributes>.activities { await a.end(nil, dismissalPolicy: .immediate) }
        guard ActivityAuthorizationInfo().areActivitiesEnabled else {
            lastMessage = "설정에서 실시간 현황(라이브 액티비티)이 꺼져 있어!"
            return
        }
        guard let cs = contentState(at: now) else { return }
        #if !WIDGET_EXTENSION   // 시작 요청은 앱 본체에서만 가능
        do {
            _ = try Activity.request(attributes: BattleAttributes(),
                                     content: .init(state: cs, staleDate: cs.deathDate),
                                     pushType: nil)
            lastPushedIndex = cs.monsterIndex
            lastMessage = "전투 시작! 잠금화면을 확인해봐"
        } catch {
            lastMessage = "라이브 액티비티 시작 실패: \(error.localizedDescription)"
        }
        #endif
    }

    /// 전투 종료 + 정산 (골드를 지갑으로)
    func stopBattle() async {
        reload()
        if let st = status() {
            state.bankedGold += st.gold
            lastMessage = "정산 완료: 처치 \(st.kills), 골드 +\(st.gold)"
        }
        state.segment = nil
        save()
        for a in Activity<BattleAttributes>.activities { await a.end(nil, dismissalPolicy: .immediate) }
    }

    func useSkill() async {
        reload()
        guard let seg = state.segment else { return }
        state.segment = BattleEngine.useSkill(seg, at: .now)
        save()
        await pushUpdate(force: true)
    }

    func upgradeAttack() async {
        reload()
        let cost = state.stats.upgradeCost
        // 진행 중인 전투 골드를 먼저 지갑으로 옮김
        if let seg = state.segment {
            let st = BattleEngine.status(seg, at: .now)
            state.bankedGold += st.gold
            var newSeg = BattleEngine.rebase(seg, at: .now, attack: seg.attack)
            newSeg.gold = 0
            state.segment = newSeg
        }
        guard state.bankedGold >= cost else {
            save()
            lastMessage = "골드가 부족해 (\(cost) 필요)"
            return
        }
        state.bankedGold -= cost
        state.stats.attackLevel += 1
        if let seg = state.segment {
            state.segment = BattleEngine.rebase(seg, at: .now, attack: state.stats.attack)
        }
        save()
        await pushUpdate(force: true)
    }

    func setRenderMode(_ m: SpriteRenderMode) async {
        state.renderMode = m
        save()
        await pushUpdate(force: true)
    }

    /// 몬스터가 바뀌었을 때만(또는 강제로) 라이브 액티비티 갱신
    func pushUpdate(force: Bool = false) async {
        guard let cs = contentState() else { return }
        if !force && cs.monsterIndex == lastPushedIndex { return }
        lastPushedIndex = cs.monsterIndex
        for a in Activity<BattleAttributes>.activities {
            await a.update(.init(state: cs, staleDate: cs.deathDate))
        }
        objectWillChange.send()
    }

    // MARK: 저장

    /// 인텐트가 다른 경로로 상태를 바꿨을 수 있으니 행동 전에 다시 읽음
    func reload() { state = GameStore.load() }
    private func save() { GameStore.save(state) }
}
