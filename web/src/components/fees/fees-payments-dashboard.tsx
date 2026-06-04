"use client";

import { useCallback, useEffect, useState } from "react";
import {
  CreditCard,
  DollarSign,
  Plus,
  RefreshCcw,
  ReceiptText,
  Search,
} from "lucide-react";
import {
  feeApi,
  paymentApi,
  paymentTransactionApi,
  salaryRecordApi,
  studentApi,
  type FeeAssignment,
  type Payment,
  type PaymentTransaction,
  type PaymentMethod,
  type SalaryRecord,
  type Student,
  ApiError,
} from "@/lib/api";
import { Badge, statusBadge } from "@/components/ui/badge";
import { Modal } from "@/components/ui/modal";
import { WorkspacePlaceholder } from "@/components/ui/workspace-placeholder";

// ─── Fee form ─────────────────────────────────────────────────────────────────
function FeeForm({
  students,
  onSave,
  onCancel,
}: {
  students: Student[];
  onSave: (data: { student: number; title: string; amount: string; due_date: string }) => Promise<void>;
  onCancel: () => void;
}) {
  const [form, setForm] = useState({
    student: String(students[0]?.id ?? ""),
    title: "",
    amount: "",
    due_date: "",
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  const inputCls = "w-full rounded-2xl border border-line/80 bg-white px-3.5 py-2.5 text-sm text-ink outline-none transition focus:border-teal-400 focus:ring-2 focus:ring-teal-400/20";

  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        setBusy(true);
        setError("");
        try { await onSave({ ...form, student: Number(form.student) }); }
        catch (err) { setError(err instanceof ApiError ? err.message : "Save failed."); }
        finally { setBusy(false); }
      }}
      className="space-y-4"
    >
      {error && <p className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-2 text-sm text-rose-600">{error}</p>}

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <label className="block text-sm font-medium text-ink">Student *</label>
          <select id="fee-student" className={`mt-1 ${inputCls}`} value={form.student} onChange={set("student")} required>
            {students.map((s) => (
              <option key={s.id} value={s.id}>{s.full_name} ({s.admission_number})</option>
            ))}
          </select>
        </div>
        <div className="sm:col-span-2">
          <label className="block text-sm font-medium text-ink">Fee Title *</label>
          <input id="fee-title" type="text" className={`mt-1 ${inputCls}`} value={form.title} onChange={set("title")} required placeholder="e.g. Tuition Fee – June 2026" />
        </div>
        <div>
          <label className="block text-sm font-medium text-ink">Amount (₹) *</label>
          <input id="fee-amount" type="number" min="0" step="0.01" className={`mt-1 ${inputCls}`} value={form.amount} onChange={set("amount")} required placeholder="12000.00" />
        </div>
        <div>
          <label className="block text-sm font-medium text-ink">Due Date *</label>
          <input id="fee-due-date" type="date" className={`mt-1 ${inputCls}`} value={form.due_date} onChange={set("due_date")} required />
        </div>
      </div>

      <div className="flex justify-end gap-3 border-t border-line/60 pt-4">
        <button type="button" onClick={onCancel} className="rounded-2xl border border-line/70 px-4 py-2 text-sm font-medium text-ink hover:bg-slate-50">Cancel</button>
        <button id="fee-save-btn" type="submit" disabled={busy} className="flex items-center gap-2 rounded-2xl bg-gradient-to-r from-teal-600 to-blue-700 px-5 py-2 text-sm font-semibold text-white shadow transition hover:-translate-y-0.5 disabled:opacity-60">
          {busy ? "Saving…" : "Create fee"}
        </button>
      </div>
    </form>
  );
}

// ─── Payment form ─────────────────────────────────────────────────────────────
function PaymentForm({
  fee,
  onSave,
  onCancel,
}: {
  fee: FeeAssignment;
  onSave: (data: { fee_assignment: number; amount_paid: string; paid_on: string; payment_method: PaymentMethod; reference_number: string }) => Promise<void>;
  onCancel: () => void;
}) {
  const [form, setForm] = useState({
    amount_paid: fee.amount,
    paid_on: new Date().toISOString().slice(0, 10),
    payment_method: "cash" as PaymentMethod,
    reference_number: "",
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  const inputCls = "w-full rounded-2xl border border-line/80 bg-white px-3.5 py-2.5 text-sm text-ink outline-none transition focus:border-teal-400 focus:ring-2 focus:ring-teal-400/20";

  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        setBusy(true);
        setError("");
        try { await onSave({ fee_assignment: fee.id, ...form }); }
        catch (err) { setError(err instanceof ApiError ? err.message : "Payment failed."); }
        finally { setBusy(false); }
      }}
      className="space-y-4"
    >
      {error && <p className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-2 text-sm text-rose-600">{error}</p>}

      <div className="rounded-2xl border border-line/60 bg-slate-50 px-4 py-3">
        <p className="text-xs text-muted">Fee</p>
        <p className="font-semibold text-ink">{fee.title}</p>
        <p className="text-sm text-muted">Total: ₹{parseFloat(fee.amount).toLocaleString("en-IN")}</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className="block text-sm font-medium text-ink">Amount Paid (₹) *</label>
          <input id="payment-amount" type="number" min="0.01" step="0.01" className={`mt-1 ${inputCls}`} value={form.amount_paid} onChange={set("amount_paid")} required />
        </div>
        <div>
          <label className="block text-sm font-medium text-ink">Payment Date *</label>
          <input id="payment-date" type="date" className={`mt-1 ${inputCls}`} value={form.paid_on} onChange={set("paid_on")} required />
        </div>
        <div>
          <label className="block text-sm font-medium text-ink">Payment Method *</label>
          <select id="payment-method" className={`mt-1 ${inputCls}`} value={form.payment_method} onChange={set("payment_method")}>
            <option value="cash">Cash</option>
            <option value="upi">UPI</option>
            <option value="card">Card</option>
            <option value="net_banking">Net banking</option>
            <option value="wallet">Wallet</option>
            <option value="bank">Bank transfer</option>
            <option value="online">Gateway</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-ink">Reference No.</label>
          <input id="payment-ref" type="text" className={`mt-1 ${inputCls}`} value={form.reference_number} onChange={set("reference_number")} placeholder="TXN123456" />
        </div>
      </div>

      <div className="flex justify-end gap-3 border-t border-line/60 pt-4">
        <button type="button" onClick={onCancel} className="rounded-2xl border border-line/70 px-4 py-2 text-sm font-medium text-ink hover:bg-slate-50">Cancel</button>
        <button id="payment-save-btn" type="submit" disabled={busy} className="flex items-center gap-2 rounded-2xl bg-gradient-to-r from-teal-600 to-blue-700 px-5 py-2 text-sm font-semibold text-white shadow transition hover:-translate-y-0.5 disabled:opacity-60">
          {busy ? "Recording…" : "Record payment"}
        </button>
      </div>
    </form>
  );
}

// ─── Main fees & payments dashboard ──────────────────────────────────────────
export function FeesPaymentsDashboard() {
  const [students, setStudents] = useState<Student[]>([]);
  const [fees, setFees] = useState<FeeAssignment[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [salaryRecords, setSalaryRecords] = useState<SalaryRecord[]>([]);
  const [transactions, setTransactions] = useState<PaymentTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [feeModal, setFeeModal] = useState(false);
  const [payModal, setPayModal] = useState<FeeAssignment | null>(null);
  const [activeTab, setActiveTab] = useState<"fees" | "payments">("fees");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [s, f, p, salaries, tx] = await Promise.all([
        studentApi.list(),
        feeApi.list(),
        paymentApi.list(),
        salaryRecordApi.list(),
        paymentTransactionApi.list(),
      ]);
      setStudents(Array.isArray(s) ? s : (s as { results: Student[] }).results ?? []);
      setFees(Array.isArray(f) ? f : (f as { results: FeeAssignment[] }).results ?? []);
      setPayments(Array.isArray(p) ? p : (p as { results: Payment[] }).results ?? []);
      setSalaryRecords(Array.isArray(salaries) ? salaries : (salaries as { results: SalaryRecord[] }).results ?? []);
      setTransactions(Array.isArray(tx) ? tx : (tx as { results: PaymentTransaction[] }).results ?? []);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const filteredFees = fees.filter((f) => {
    const student = students.find((s) => s.id === f.student);
    const q = search.toLowerCase();
    const matchSearch = !q || f.title.toLowerCase().includes(q) || student?.full_name.toLowerCase().includes(q) || student?.admission_number.toLowerCase().includes(q);
    const matchStatus = !filterStatus || f.status === filterStatus;
    return matchSearch && matchStatus;
  });

  // Summary metrics
  const totalAssigned = fees.reduce((acc, f) => acc + parseFloat(f.amount), 0);
  const totalCollected = payments.reduce((acc, p) => acc + parseFloat(p.amount_paid), 0);
  const totalPending = fees.filter((f) => f.status === "pending" || f.status === "partial").reduce((acc, f) => acc + parseFloat(f.amount), 0);
  const today = new Date().toISOString().slice(0, 10);
  const todayCollection = payments
    .filter((payment) => payment.paid_on === today)
    .reduce((acc, payment) => acc + parseFloat(payment.amount_paid), 0);
  const onlineCollection = payments
    .filter((payment) => ["online", "upi", "card", "net_banking", "wallet"].includes(payment.payment_method))
    .reduce((acc, payment) => acc + parseFloat(payment.amount_paid), 0);
  const offlineCollection = payments
    .filter((payment) => ["cash", "bank"].includes(payment.payment_method))
    .reduce((acc, payment) => acc + parseFloat(payment.amount_paid), 0);
  const salaryPayable = salaryRecords
    .filter((salary) => salary.payment_status !== "paid")
    .reduce((acc, salary) => acc + parseFloat(salary.final_salary), 0);

  async function handleCreateFee(data: { student: number; title: string; amount: string; due_date: string }) {
    await feeApi.create(data as Parameters<typeof feeApi.create>[0]);
    setFeeModal(false);
    load();
  }

  async function handleRecordPayment(data: Parameters<typeof paymentApi.create>[0]) {
    await paymentApi.create(data);
    setPayModal(null);
    load();
  }

  if (loading) {
    return <WorkspacePlaceholder title="Fees dashboard" detail="Preparing dues, payments, and student accounts." />;
  }

  return (
    <div className="space-y-6">
      <section className="surface p-5 shadow-soft">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <span className="section-kicker">
              <ReceiptText size={14} />
              Finance desk
            </span>
            <h1 className="display-font mt-3 text-2xl font-semibold text-ink">Fees and payments</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
              Assign fees, capture payments, filter outstanding dues, and review collection health from one finance workspace.
            </p>
          </div>
          <button
            type="button"
            onClick={load}
            className="flex items-center gap-2 rounded-lg border border-line/70 bg-white px-4 py-2 text-sm font-medium text-muted hover:bg-slate-50 hover:text-ink"
          >
            <RefreshCcw size={14} /> Refresh
          </button>
        </div>
      </section>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="surface rounded-3xl p-5 shadow-soft">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted">Total Assigned</p>
          <p className="display-font mt-3 text-3xl font-bold text-ink">₹{totalAssigned.toLocaleString("en-IN")}</p>
          <p className="mt-1 text-xs text-muted">{fees.length} fee records</p>
        </div>
        <div className="surface rounded-3xl p-5 shadow-soft">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted">Collected</p>
          <p className="display-font mt-3 text-3xl font-bold text-emerald-600">₹{totalCollected.toLocaleString("en-IN")}</p>
          <p className="mt-1 text-xs text-muted">{payments.length} payments</p>
        </div>
        <div className="surface rounded-3xl p-5 shadow-soft">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted">Outstanding</p>
          <p className="display-font mt-3 text-3xl font-bold text-rose-600">₹{totalPending.toLocaleString("en-IN")}</p>
          <p className="mt-1 text-xs text-muted">{fees.filter((f) => ["pending", "partial", "overdue"].includes(f.status)).length} pending</p>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="surface rounded-3xl p-5 shadow-soft">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted">Today</p>
          <p className="display-font mt-3 text-3xl font-bold text-blue-700">â‚¹{todayCollection.toLocaleString("en-IN")}</p>
          <p className="mt-1 text-xs text-muted">Collection recorded today</p>
        </div>
        <div className="surface rounded-3xl p-5 shadow-soft">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted">Online</p>
          <p className="display-font mt-3 text-3xl font-bold text-emerald-700">â‚¹{onlineCollection.toLocaleString("en-IN")}</p>
          <p className="mt-1 text-xs text-muted">UPI, card, net banking, wallet, gateway</p>
        </div>
        <div className="surface rounded-3xl p-5 shadow-soft">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted">Offline</p>
          <p className="display-font mt-3 text-3xl font-bold text-slate-700">â‚¹{offlineCollection.toLocaleString("en-IN")}</p>
          <p className="mt-1 text-xs text-muted">Cash and bank entries</p>
        </div>
        <div className="surface rounded-3xl p-5 shadow-soft">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted">Salary Payable</p>
          <p className="display-font mt-3 text-3xl font-bold text-amber-700">â‚¹{salaryPayable.toLocaleString("en-IN")}</p>
          <p className="mt-1 text-xs text-muted">{salaryRecords.length} salary records</p>
        </div>
        <div className="surface rounded-3xl p-5 shadow-soft">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted">Transactions</p>
          <p className="display-font mt-3 text-3xl font-bold text-ink">{transactions.length}</p>
          <p className="mt-1 text-xs text-muted">{transactions.filter((tx) => tx.status === "failed").length} failed</p>
        </div>
      </div>

      {error && (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {error} <button className="underline ml-2" onClick={load}>Retry</button>
        </div>
      )}

      {/* Tab bar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="grid w-full grid-cols-2 gap-2 sm:w-auto sm:flex">
          {(["fees", "payments"] as const).map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setActiveTab(t)}
              className={`flex items-center gap-2 rounded-2xl px-4 py-2 text-sm font-medium capitalize transition ${
                activeTab === t ? "bg-ink text-white shadow" : "border border-line/70 bg-white text-muted hover:bg-slate-50 hover:text-ink"
              }`}
            >
              {t === "fees" ? <ReceiptText size={14} /> : <CreditCard size={14} />}
              {t === "fees" ? "Fee Assignments" : "Payments"}
            </button>
          ))}
        </div>
        <div className="flex w-full flex-wrap gap-2 sm:w-auto">
          <button
            type="button"
            onClick={load}
            className="flex items-center gap-2 rounded-2xl border border-line/70 bg-white px-4 py-2 text-sm font-medium text-muted hover:bg-slate-50 hover:text-ink"
          >
            <RefreshCcw size={14} /> Refresh
          </button>
          {activeTab === "fees" && (
            <button
              id="add-fee-btn"
              type="button"
              onClick={() => setFeeModal(true)}
              className="flex items-center gap-2 rounded-2xl bg-gradient-to-r from-teal-600 to-blue-700 px-4 py-2 text-sm font-semibold text-white shadow transition hover:-translate-y-0.5"
            >
              <Plus size={14} /> Assign Fee
            </button>
          )}
        </div>
      </div>

      {/* Fees table */}
      {activeTab === "fees" && (
        <div className="surface overflow-hidden shadow-soft">
          <div className="flex flex-wrap items-center gap-3 border-b border-line/60 px-4 py-4 sm:px-5">
            <div className="relative min-w-0 flex-1 basis-full sm:basis-72">
              <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted" />
              <input
                id="fee-search"
                type="search"
                placeholder="Search by fee title or student name…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full rounded-2xl border border-line/70 bg-white py-2.5 pl-9 pr-4 text-sm text-ink outline-none focus:border-teal-400 focus:ring-2 focus:ring-teal-400/20"
              />
            </div>
            <select
              id="fee-filter-status"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="w-full rounded-2xl border border-line/70 bg-white px-3.5 py-2.5 text-sm text-ink outline-none focus:border-teal-400 sm:w-auto"
            >
              <option value="">All statuses</option>
              <option value="pending">Pending</option>
              <option value="partial">Partial</option>
              <option value="paid">Paid</option>
              <option value="overdue">Overdue</option>
            </select>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line/60 bg-slate-50">
                  {["Student", "Fee Title", "Amount", "Due Date", "Status", "Actions"].map((h) => (
                    <th key={h} className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredFees.length === 0 ? (
                  <tr><td colSpan={6} className="px-5 py-12 text-center text-muted">No fee records found.</td></tr>
                ) : filteredFees.map((f) => {
                  const student = students.find((s) => s.id === f.student);
                  return (
                    <tr key={f.id} className="border-b border-line/40 hover:bg-slate-50/60">
                      <td className="px-5 py-3.5">
                        <p className="font-semibold text-ink">{student?.full_name ?? "—"}</p>
                        <p className="text-xs font-mono text-muted">{student?.admission_number}</p>
                      </td>
                      <td className="px-5 py-3.5 text-ink">{f.title}</td>
                      <td className="px-5 py-3.5 font-semibold text-ink">₹{parseFloat(f.amount).toLocaleString("en-IN")}</td>
                      <td className="px-5 py-3.5 text-muted">{f.due_date}</td>
                      <td className="px-5 py-3.5"><Badge variant={statusBadge(f.status)}>{f.status}</Badge></td>
                      <td className="px-5 py-3.5">
                        {f.status !== "paid" && (
                          <button
                            type="button"
                            onClick={() => setPayModal(f)}
                            className="flex items-center gap-1.5 rounded-xl border border-teal-200 bg-teal-50 px-3 py-1.5 text-xs font-medium text-teal-700 hover:bg-teal-100 transition"
                          >
                            <DollarSign size={12} />
                            Record Payment
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="border-t border-line/60 px-5 py-3 text-xs text-muted">
            {filteredFees.length} of {fees.length} fee records
          </div>
        </div>
      )}

      {/* Payments table */}
      {activeTab === "payments" && (
        <div className="surface overflow-hidden shadow-soft">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line/60 bg-slate-50">
                  {["Fee", "Student", "Amount Paid", "Date", "Method", "Reference"].map((h) => (
                    <th key={h} className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {payments.length === 0 ? (
                  <tr><td colSpan={6} className="px-5 py-12 text-center text-muted">No payments recorded yet.</td></tr>
                ) : payments.map((p) => {
                  const fee = fees.find((f) => f.id === p.fee_assignment);
                  const student = students.find((s) => s.id === fee?.student);
                  return (
                    <tr key={p.id} className="border-b border-line/40 hover:bg-slate-50/60">
                      <td className="px-5 py-3.5 text-ink">{fee?.title ?? "—"}</td>
                      <td className="px-5 py-3.5 font-semibold text-ink">{student?.full_name ?? "—"}</td>
                      <td className="px-5 py-3.5 font-semibold text-emerald-600">₹{parseFloat(p.amount_paid).toLocaleString("en-IN")}</td>
                      <td className="px-5 py-3.5 text-muted">{p.paid_on}</td>
                      <td className="px-5 py-3.5"><Badge variant="info">{p.payment_method}</Badge></td>
                      <td className="px-5 py-3.5 font-mono text-xs text-muted">{p.reference_number || "—"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modals */}
      <Modal open={feeModal} onClose={() => setFeeModal(false)} title="Assign Fee to Student" size="md">
        <FeeForm students={students} onSave={handleCreateFee} onCancel={() => setFeeModal(false)} />
      </Modal>

      {payModal && (
        <Modal open={!!payModal} onClose={() => setPayModal(null)} title="Record Payment" size="md">
          <PaymentForm fee={payModal} onSave={handleRecordPayment} onCancel={() => setPayModal(null)} />
        </Modal>
      )}
    </div>
  );
}
