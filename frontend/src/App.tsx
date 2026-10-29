import Box from "@mui/material/Box";
import { useColorScheme } from "@mui/material/styles";
import useMediaQuery from "@mui/material/useMediaQuery";
import { useCallback, useEffect, useState } from "react";
import { api, type HealthResponse } from "./api";
import { FeedbackProvider } from "./components/feedback";
import { Rail, TopBar } from "./components/Shell";
import { WatchPanel, WatchPanelButton, WatchlistsProvider } from "./components/Watchlists";
import { PAGES, TIMEFRAMES, type PageKey } from "./lib/nav";
import { readPref, readRecents, rememberRecent, writePref } from "./lib/storage";
import CalendarPage from "./pages/Calendar";
import Desk from "./pages/Desk";
import Arena from "./pages/Arena";
import Backtests from "./pages/Backtests";
import Hype from "./pages/Hype";
import JobRuns from "./pages/JobRuns";
import Journal from "./pages/Journal";
import Paper from "./pages/Paper";
import Picks from "./pages/Picks";
import Strategies from "./pages/Strategies";
import Signals from "./pages/Signals";
import Wallets from "./pages/Wallets";
import Watchlist from "./pages/Watchlist";

/** WL-101: no page in the address opens the page used last. */
function pageFromHash(): PageKey {
  // Support #/signals/{id} detail routes from the multi-analyze merge.
  const name = window.location.hash.replace(/^#\/?/, "").split("/")[0] || (readPref("cca_page") ?? "");
  return name in PAGES ? (name as PageKey) : "desk";
}

function initialTimeframe(): string {
  const tf = readPref("cca_tf");
  return tf && (TIMEFRAMES as readonly string[]).includes(tf) ? tf : "1h";
}

export default function App() {
  const recent = readRecents()[0];
  const [page, setPage] = useState<PageKey>(pageFromHash);
  const [symbol, setSymbol] = useState(recent?.symbol ?? "SOLUSDT");
  const [exchange, setExchange] = useState(recent?.exchange ?? "BINANCE");
  const [tvSymbol, setTvSymbol] = useState(recent?.tv_symbol ?? "BINANCE:SOLUSDT");
  const [timeframe, setTimeframe] = useState(initialTimeframe);
  const [pairPick, setPairPick] = useState(0); // WL-131: every pick, also of the same pair, asks the desk chat for a timeframe
  const [folded, setFolded] = useState(() => readPref("cca_rail_folded") === "1");
  // WL-093: the Arena (and since WL-128 the picks) has its own section sidebar, so the main rail folds there without touching the saved choice.
  const [arenaRailOpen, setArenaRailOpen] = useState(false);
  const sectioned = page === "arena" || page === "picks";
  const railFolded = sectioned ? !arenaRailOpen : folded;
  const [navOpen, setNavOpen] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState(false);
  const [journalOpen, setJournalOpen] = useState(0);
  const [signalsOpen, setSignalsOpen] = useState(0);
  const [journalVersion, setJournalVersion] = useState(0);
  const [signalsVersion, setSignalsVersion] = useState(0);

  const desktop = useMediaQuery((t) => t.breakpoints.up("md"), { noSsr: true });
  const { mode, systemMode } = useColorScheme();
  const dark = (mode === "system" ? systemMode : mode) === "dark";

  useEffect(() => {
    const onHash = () => {
      setPage(pageFromHash());
      setNavOpen(false);
    };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  useEffect(() => writePref("cca_page", page), [page]);

  useEffect(() => {
    api
      .health()
      .then((h) => setHealth(h))
      .catch(() => setHealthError(true));
  }, []);

  const pickPair = useCallback(
    (sym: string, ex?: string, tv?: string) => {
      const s = sym.trim().toUpperCase();
      if (!s) return;
      const e = (ex ?? exchange).toUpperCase();
      const t = (tv ?? `${e}:${s}`).toUpperCase();
      setSymbol(s);
      setExchange(e);
      setTvSymbol(t);
      rememberRecent({ symbol: s, exchange: e, tv_symbol: t });
      setPairPick((n) => n + 1);
    },
    [exchange],
  );

  const goTo = (p: PageKey) => {
    window.location.hash = `#/${p}`;
  };

  const openOnDesk = (s: string, ex?: string, tv?: string) => {
    pickPair(s, ex, tv);
    goTo("desk");
  };

  const onJournalStats = useCallback((s: { open?: number }) => setJournalOpen(s.open ?? 0), []);
  const onSignalStats = useCallback((s: { open?: number }) => setSignalsOpen(s.open ?? 0), []);

  return (
    <FeedbackProvider>
      <WatchlistsProvider>
        <Box sx={{ display: "flex", minHeight: "100vh", bgcolor: "background.default" }}>
          <Rail
            desktop={desktop}
            mobileOpen={navOpen}
            onCloseMobile={() => setNavOpen(false)}
            page={page}
            health={health}
            healthError={healthError}
            journalOpen={journalOpen}
            signalsOpen={signalsOpen}
            folded={railFolded}
            onToggleFold={() => {
              if (sectioned) {
                setArenaRailOpen(!arenaRailOpen);
                return;
              }
              writePref("cca_rail_folded", folded ? "0" : "1");
              setFolded(!folded);
            }}
          />
          <Box sx={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}>
            <TopBar
              page={page}
              symbol={symbol}
              exchange={exchange}
              timeframe={timeframe}
              desktop={desktop}
              onMenu={() => setNavOpen(true)}
              onExchange={(ex) => pickPair(symbol, ex)}
              onTimeframe={(tf) => {
                writePref("cca_tf", tf);
                setTimeframe(tf);
              }}
              onPickPair={openOnDesk}
              onPickPage={goTo}
              actions={<WatchPanelButton />}
            />
            {/* Pages stay mounted so the desk keeps its plan and chat while you browse. */}
            <Box component="main" sx={{ p: { xs: 2, md: 3 }, minWidth: 0, flex: 1 }}>
              <Box hidden={page !== "desk"}>
                <Desk
                  symbol={symbol}
                  exchange={exchange}
                  tvSymbol={tvSymbol}
                  timeframe={timeframe}
                  pairPick={pairPick}
                  dark={dark}
                  active={page === "desk"}
                  onSignalRecorded={() => setSignalsVersion((v) => v + 1)}
                  onJournalChanged={() => setJournalVersion((v) => v + 1)}
                  onTimeframe={(tf) => {
                    writePref("cca_tf", tf);
                    setTimeframe(tf);
                  }}
                />
              </Box>
              <Box hidden={page !== "watchlist"}>
                <Watchlist timeframe={timeframe} onOpen={(s, ex) => openOnDesk(s, ex ?? "BINANCE")} />
              </Box>
              <Box hidden={page !== "calendar"}>
                <CalendarPage active={page === "calendar"} onOpenPair={openOnDesk} />
              </Box>
              <Box hidden={page !== "picks"}>
                <Picks active={page === "picks"} onOpenPair={openOnDesk} />
              </Box>
              <Box hidden={page !== "hype"}>
                <Hype active={page === "hype"} onOpenPair={openOnDesk} />
              </Box>
              <Box hidden={page !== "strategies"}>
                <Strategies active={page === "strategies"} />
              </Box>
              <Box hidden={page !== "backtests"}>
                <Backtests active={page === "backtests"} />
              </Box>
              <Box hidden={page !== "arena"}>
                <Arena active={page === "arena"} />
              </Box>
              <Box hidden={page !== "paper"}>
                <Paper active={page === "paper"} />
              </Box>
              <Box hidden={page !== "wallets"}>
                <Wallets active={page === "wallets"} />
              </Box>
              <Box hidden={page !== "journal"}>
                <Journal active={page === "journal"} version={journalVersion} onStats={onJournalStats} />
              </Box>
              <Box hidden={page !== "signals"}>
                <Signals active={page === "signals"} version={signalsVersion} onStats={onSignalStats} />
              </Box>
              <Box hidden={page !== "jobruns"}>
                <JobRuns active={page === "jobruns"} />
              </Box>
            </Box>
          </Box>
          {/* WL-152: the watchlists docked on the right, like TradingView; the page shrinks beside it. */}
          <WatchPanel desktop={desktop} onOpenPair={(s, ex) => openOnDesk(s, ex ?? "BINANCE")} onManage={() => goTo("watchlist")} />
        </Box>
      </WatchlistsProvider>
    </FeedbackProvider>
  );
}
