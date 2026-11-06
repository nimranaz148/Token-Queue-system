import Link from "next/link";
import {
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  Check,
  Clock3,
  Monitor,
  MoveRight,
  ShieldCheck,
  Smartphone,
  Stethoscope,
  UsersRound,
} from "lucide-react";

const workflow = [
  {
    number: "01",
    icon: Smartphone,
    title: "Mareez token leta hai",
    description: "Clinic ke link se doctor aur din chunta hai. App ya account ki zaroorat nahi.",
    tone: "bg-accent-subtle text-accent",
  },
  {
    number: "02",
    icon: UsersRound,
    title: "Sab aik queue mein",
    description: "Online booking aur reception ke walk-in tokens aik hi tarteeb mein rehte hain.",
    tone: "bg-info-subtle text-info",
  },
  {
    number: "03",
    icon: Stethoscope,
    title: "Doctor NEXT dabata hai",
    description: "Doctor apne panel se agla mareez bulata aur zaroori history dekhta hai.",
    tone: "bg-warning-subtle text-warning",
  },
  {
    number: "04",
    icon: Monitor,
    title: "Queue live update hoti hai",
    description: "Token number patient ke phone aur waiting-room TV par nazar aata hai.",
    tone: "bg-success-subtle text-success",
  },
];

const benefits = [
  "Mareez ko apna number foran milta hai",
  "Reception ka register aik shared list banta hai",
  "Owner ko roz ka queue overview milta hai",
];

export default function HomePage() {
  return (
    <main className="min-h-screen overflow-hidden bg-canvas text-fg">
      <header className="mx-auto flex w-full max-w-7xl items-center justify-between px-5 py-5 sm:px-8 lg:px-10">
        <Link href="/" className="group flex items-center gap-3" aria-label="Clinic Token & Queue home">
          <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent text-fg-inverse shadow-sm transition-transform group-hover:-rotate-3">
            <Stethoscope className="h-5 w-5" aria-hidden="true" />
          </span>
          <span className="leading-tight">
            <span className="block text-sm font-semibold tracking-tight">Clinic Queue</span>
            <span className="mt-1 block text-2xs font-medium uppercase tracking-[0.16em] text-fg-muted">Token system</span>
          </span>
        </Link>

        <nav aria-label="Main navigation" className="flex items-center gap-3 sm:gap-7">
          <Link href="#how-it-works" className="hidden text-sm font-medium text-fg-muted transition-colors hover:text-accent sm:inline-flex">
            Kaise kaam karta hai
          </Link>
          <Link
            href="/login"
            className="inline-flex h-10 items-center gap-2 rounded-md bg-accent px-4 text-sm font-semibold text-fg-inverse shadow-sm transition-all hover:-translate-y-0.5 hover:bg-accent-hover hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2"
          >
            Staff Login <ArrowUpRight className="h-4 w-4" aria-hidden="true" />
          </Link>
        </nav>
      </header>

      <section className="relative mx-auto grid w-full max-w-7xl items-center gap-12 px-5 pb-16 pt-8 sm:px-8 sm:pb-20 sm:pt-12 lg:grid-cols-[0.95fr_1.05fr] lg:gap-8 lg:px-10 lg:pb-28 lg:pt-14">
        <div className="relative z-10 max-w-2xl">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-accent-border bg-surface px-3 py-1.5 text-2xs font-semibold uppercase tracking-[0.15em] text-accent">
            <span className="h-1.5 w-1.5 rounded-full bg-success" /> Clinic token &amp; queue system
          </div>
          <h1 className="font-display text-display font-medium leading-[1.04] tracking-[-0.045em] text-fg">
            <span className="mb-3 block font-sans text-xs font-semibold uppercase tracking-[0.18em] text-accent sm:text-sm">
              Clinic Token &amp; Queue SaaS
            </span>
            Clinic ki line,
            <br />
            <span className="text-accent">ab sab ko maloom.</span>
          </h1>
          <p className="mt-6 max-w-xl text-base leading-7 text-fg-muted sm:text-lg sm:leading-8">
            Online token se doctor ke NEXT tak — clinic ki queue, mareez aur staff aik hi flow mein.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
            <Link
              href="/login"
              className="inline-flex h-12 items-center justify-center gap-2 rounded-md bg-accent px-6 text-sm font-semibold text-fg-inverse shadow-md transition-all hover:-translate-y-0.5 hover:bg-accent-hover hover:shadow-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2"
            >
              Staff portal kholein <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
            <Link
              href="#how-it-works"
              className="inline-flex h-12 items-center justify-center gap-2 rounded-md border border-border-strong bg-surface px-5 text-sm font-semibold text-fg transition-colors hover:bg-surface-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2"
            >
              Product dekhein <ArrowDownRight className="h-4 w-4" aria-hidden="true" />
            </Link>
          </div>
          <div className="mt-8 flex flex-wrap gap-x-5 gap-y-2 text-xs font-medium text-fg-muted sm:mt-10">
            <span className="inline-flex items-center gap-1.5"><Check className="h-3.5 w-3.5 text-success" /> Mareez login ke baghair</span>
            <span className="inline-flex items-center gap-1.5"><Check className="h-3.5 w-3.5 text-success" /> Online + walk-in queue</span>
          </div>
        </div>

        <div className="relative mx-auto w-full max-w-[620px] lg:ml-auto">
          <div className="absolute -right-4 -top-8 h-40 w-40 rounded-full border border-accent-border sm:-right-8 sm:-top-12 sm:h-64 sm:w-64" aria-hidden="true" />
          <div className="absolute -bottom-9 -left-5 h-28 w-28 rounded-full bg-warning-subtle sm:-bottom-12 sm:-left-9 sm:h-40 sm:w-40" aria-hidden="true" />

          <div className="relative rounded-lg border border-border bg-surface p-2.5 shadow-lg sm:rounded-lg sm:p-3">
            <div className="overflow-hidden rounded-md bg-accent">
              <div className="flex items-center justify-between border-b border-fg-inverse/15 px-4 py-3.5 text-fg-inverse sm:px-6 sm:py-4">
                <div className="flex items-center gap-3">
                  <span className="flex h-9 w-9 items-center justify-center rounded-md bg-surface/10"><Stethoscope className="h-4 w-4" aria-hidden="true" /></span>
                  <div>
                    <p className="text-sm font-semibold">Aaj ki Queue</p>
                    <p className="mt-0.5 text-2xs text-fg-inverse/70">Doctor panel · sample view</p>
                  </div>
                </div>
                <span className="inline-flex items-center gap-1.5 rounded-full border border-fg-inverse/20 px-2.5 py-1 text-2xs font-semibold uppercase tracking-[0.12em] text-fg-inverse/85">
                  <span className="h-1.5 w-1.5 rounded-full bg-success-border" /> Demo
                </span>
              </div>

              <div className="grid gap-3 p-4 sm:grid-cols-[1.1fr_0.9fr] sm:gap-4 sm:p-6">
                <div className="flex min-h-52 flex-col justify-between rounded-md bg-surface p-4 sm:min-h-60 sm:p-5">
                  <div className="flex items-center justify-between">
                    <span className="text-2xs font-semibold uppercase tracking-[0.15em] text-fg-muted">Abhi chal raha</span>
                    <span className="rounded-full bg-success-subtle px-2 py-1 text-2xs font-semibold text-success">Serving</span>
                  </div>
                  <div className="py-3 text-center">
                    <span className="font-mono text-6xl font-medium tracking-[-0.07em] text-fg sm:text-7xl">#12</span>
                    <p className="mt-2 text-xs text-fg-muted">Agla number</p>
                  </div>
                  <div className="flex items-center justify-between border-t border-border pt-3">
                    <span className="text-xs font-medium text-fg-muted">NEXT</span>
                    <div className="flex items-center gap-1.5 font-mono text-xs font-semibold text-accent">
                      <span>#13</span><span className="text-fg-subtle">·</span><span>#14</span><span className="text-fg-subtle">·</span><span>#15</span>
                    </div>
                  </div>
                </div>

                <div className="flex flex-col gap-3">
                  <div className="flex flex-1 flex-col justify-between rounded-md border border-fg-inverse/15 bg-surface/10 p-4 text-fg-inverse sm:p-5">
                    <div className="flex items-center justify-between text-fg-inverse/75">
                      <span className="text-2xs font-medium">Patient link</span>
                      <Smartphone className="h-4 w-4" aria-hidden="true" />
                    </div>
                    <div>
                      <p className="font-mono text-4xl font-medium tracking-tight">#18</p>
                      <p className="mt-1 text-xs text-fg-inverse/75">6 log pehle · andaazan 35 min</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 rounded-md bg-surface p-3.5">
                    <span className="flex h-9 w-9 items-center justify-center rounded-md bg-accent-subtle text-accent"><Clock3 className="h-4 w-4" aria-hidden="true" /></span>
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-semibold text-fg">Queue status</p>
                      <p className="mt-0.5 text-2xs text-fg-muted">Phone par live update</p>
                    </div>
                    <MoveRight className="h-4 w-4 text-accent" aria-hidden="true" />
                  </div>
                </div>
              </div>
            </div>
            <p className="px-2 pb-1 pt-3 text-center text-2xs text-fg-muted">Sample interface · numbers are illustrative</p>
          </div>

          <div className="absolute -left-4 top-[48%] hidden -translate-x-1/2 items-center gap-2 rounded-md border border-border bg-surface px-3 py-2.5 text-xs font-medium text-fg shadow-md xl:flex">
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-success-subtle text-success"><Check className="h-4 w-4" aria-hidden="true" /></span>
            Doctor ne NEXT dabaya
          </div>
        </div>
      </section>

      <section className="border-y border-border bg-surface/70" aria-label="Product benefits">
        <div className="mx-auto grid max-w-7xl gap-4 px-5 py-6 sm:grid-cols-3 sm:px-8 lg:px-10">
          {benefits.map((benefit, index) => (
            <div key={benefit} className="flex items-center gap-3 sm:justify-center">
              <span className="font-mono text-2xs font-semibold text-accent">0{index + 1}</span>
              <span className="text-xs font-medium leading-5 text-fg sm:text-sm">{benefit}</span>
            </div>
          ))}
        </div>
      </section>

      <section id="how-it-works" className="mx-auto max-w-7xl px-5 py-20 sm:px-8 sm:py-24 lg:px-10 lg:py-28">
        <div className="mb-10 flex flex-col gap-5 sm:mb-14 sm:flex-row sm:items-end sm:justify-between">
          <div className="max-w-2xl">
            <p className="text-2xs font-semibold uppercase tracking-[0.18em] text-accent">Aik seedha flow</p>
            <h2 className="mt-4 font-display text-4xl font-medium leading-tight tracking-[-0.035em] text-fg sm:text-5xl">
              Parchi se live queue tak.
            </h2>
          </div>
          <p className="max-w-sm text-sm leading-6 text-fg-muted">
            Har role ko apna saaf view milta hai — mareez se waiting-room TV tak.
          </p>
        </div>

        <div className="grid overflow-hidden rounded-lg border border-border bg-surface sm:grid-cols-2 lg:grid-cols-4">
          {workflow.map((step, index) => {
            const Icon = step.icon;
            return (
              <article key={step.number} className="relative border-b border-border p-5 last:border-b-0 sm:p-6 lg:border-b-0 lg:border-r lg:last:border-r-0">
                <div className="mb-10 flex items-center justify-between">
                  <span className={`flex h-11 w-11 items-center justify-center rounded-md ${step.tone}`}>
                    <Icon className="h-5 w-5" aria-hidden="true" />
                  </span>
                  <span className="font-mono text-xs text-fg-subtle">{step.number}</span>
                </div>
                <h3 className="text-base font-semibold tracking-tight text-fg">{step.title}</h3>
                <p className="mt-2 text-sm leading-6 text-fg-muted">{step.description}</p>
                {index < workflow.length - 1 && (
                  <ArrowRight className="absolute right-5 top-8 hidden h-4 w-4 text-border-strong lg:block" aria-hidden="true" />
                )}
              </article>
            );
          })}
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-12 px-5 pb-20 sm:px-8 sm:pb-24 lg:grid-cols-[0.9fr_1.1fr] lg:items-center lg:gap-20 lg:px-10 lg:pb-28">
        <div>
          <p className="text-2xs font-semibold uppercase tracking-[0.18em] text-accent">Owner ka rozana overview</p>
          <h2 className="mt-4 max-w-xl font-display text-4xl font-medium leading-tight tracking-[-0.035em] text-fg sm:text-5xl">
            Aaj ka haal, aik nazar mein.
          </h2>
          <p className="mt-5 max-w-lg text-sm leading-7 text-fg-muted sm:text-base">
            Patients seen, average wait, no-shows aur online token share — clinic owner apni daily report phone par dekh sakta hai.
          </p>
          <ul className="mt-7 space-y-3">
            {[
              "Aaj ke patients aur average wait",
              "No-show count aur online booking share",
              "Saat din ka queue trend",
            ].map((item) => (
              <li key={item} className="flex items-start gap-3 text-sm text-fg">
                <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-success-subtle text-success"><Check className="h-3 w-3" aria-hidden="true" /></span>
                {item}
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-lg border border-border bg-surface p-4 shadow-md sm:p-6">
          <div className="flex items-start justify-between gap-4 border-b border-border pb-4">
            <div>
              <p className="text-xs font-semibold text-fg">Roz ki Report</p>
              <p className="mt-1 text-2xs text-fg-muted">Sample dashboard · daily view</p>
            </div>
            <span className="rounded-full bg-accent-subtle px-2.5 py-1 text-2xs font-semibold text-accent">DEMO</span>
          </div>
          <div className="grid grid-cols-2 gap-3 py-4 sm:grid-cols-4">
            {[
              { label: "Patients", value: "54" },
              { label: "Avg wait", value: "14m" },
              { label: "No-shows", value: "06" },
              { label: "Online", value: "38%" },
            ].map((metric) => (
              <div key={metric.label} className="rounded-md bg-surface-sunken p-3">
                <p className="text-2xs text-fg-muted">{metric.label}</p>
                <p className="mt-2 font-mono text-xl font-semibold tracking-tight text-fg">{metric.value}</p>
              </div>
            ))}
          </div>
          <div className="rounded-md border border-border p-4">
            <div className="mb-4 flex items-center justify-between">
              <p className="text-xs font-semibold text-fg">Pichlay 7 din</p>
              <span className="inline-flex items-center gap-1 text-2xs text-fg-muted"><ArrowUpRight className="h-3.5 w-3.5 text-success" /> Patients seen</span>
            </div>
            <div className="flex h-24 items-end gap-2 sm:h-28 sm:gap-3" aria-label="Illustrative seven-day report chart">
              {[42, 56, 48, 72, 60, 84, 68].map((height, index) => (
                <div key={index} className="flex h-full flex-1 items-end">
                  <div className={`w-full rounded-t-sm ${index === 5 ? "bg-chart-1" : "bg-chart-2/70"}`} style={{ height: `${height}%` }} />
                </div>
              ))}
            </div>
            <p className="mt-3 text-right text-2xs text-fg-subtle">Illustrative values</p>
          </div>
        </div>
      </section>

      <section className="px-5 pb-16 sm:px-8 sm:pb-20 lg:px-10">
        <div className="mx-auto flex max-w-7xl flex-col gap-7 overflow-hidden rounded-lg bg-accent px-6 py-8 text-fg-inverse sm:px-10 sm:py-10 lg:flex-row lg:items-center lg:justify-between lg:px-14">
          <div className="max-w-2xl">
            <p className="text-2xs font-semibold uppercase tracking-[0.18em] text-fg-inverse/70">Clinic staff ke liye</p>
            <h2 className="mt-3 font-display text-3xl font-medium tracking-[-0.03em] sm:text-4xl">Apna clinic portal kholein.</h2>
            <p className="mt-3 text-sm leading-6 text-fg-inverse/75">Owner, doctor aur reception staff apne role ke mutabiq sign in karte hain.</p>
          </div>
          <Link
            href="/login"
            className="inline-flex h-12 shrink-0 items-center justify-center gap-2 rounded-md bg-surface px-5 text-sm font-semibold text-accent shadow-sm transition-all hover:-translate-y-0.5 hover:bg-surface-hover hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-fg-inverse focus-visible:ring-offset-2 focus-visible:ring-offset-accent"
          >
            Staff Login <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
        </div>
      </section>

      <footer className="border-t border-border">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-5 py-6 text-xs text-fg-muted sm:flex-row sm:items-center sm:justify-between sm:px-8 lg:px-10">
          <p>Clinic Token &amp; Queue SaaS</p>
          <div className="flex items-center gap-2"><ShieldCheck className="h-3.5 w-3.5 text-accent" aria-hidden="true" /> Clinic-scoped access · Staff sign in required</div>
          <Link href="/login" className="font-semibold text-accent transition-colors hover:text-accent-hover">Staff Login</Link>
        </div>
      </footer>
    </main>
  );
}
