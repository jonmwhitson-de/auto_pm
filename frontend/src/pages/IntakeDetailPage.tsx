import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Loader2, ArrowLeft, Sparkles, ArrowRight, MessageSquare,
  CheckCircle, AlertCircle, Users, FileText, Target, Shield,
  GitMerge, ExternalLink
} from 'lucide-react';
import {
  getIntake, processIntake, convertIntakeToProject, answerQuestion,
  type IntakeDetail, type ClarifyingQuestion
} from '../api/client';
import clsx from 'clsx';

const statusColors: Record<string, string> = {
  new: 'bg-blue-100 text-blue-700',
  triaging: 'bg-yellow-100 text-yellow-700',
  needs_clarification: 'bg-orange-100 text-orange-700',
  ready: 'bg-green-100 text-green-700',
  converted: 'bg-purple-100 text-purple-700',
  duplicate: 'bg-gray-100 text-gray-600',
  rejected: 'bg-red-100 text-red-700',
};

export default function IntakeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: intake, isLoading } = useQuery({
    queryKey: ['intake', id],
    queryFn: () => getIntake(Number(id)),
  });

  const processMutation = useMutation({
    mutationFn: () => processIntake(Number(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intake', id] });
    },
  });

  const convertMutation = useMutation({
    mutationFn: () => convertIntakeToProject(Number(id)),
    onSuccess: (data) => {
      navigate(`/projects/${data.project_id}`);
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  if (!intake) {
    return <div>Intake not found</div>;
  }

  const canProcess = intake.status === 'new';
  const canConvert = intake.status === 'ready' || intake.status === 'needs_clarification';

  return (
    <div>
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Link to="/intake" className="text-gray-500 hover:text-gray-700">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900">{intake.title}</h1>
          <div className="flex items-center gap-3 mt-1 text-sm text-gray-500">
            <span className={clsx('px-2 py-0.5 rounded-full', statusColors[intake.status])}>
              {intake.status.replace('_', ' ')}
            </span>
            <span>Source: {intake.source}</span>
            {intake.source_author && <span>From: {intake.source_author}</span>}
          </div>
        </div>
        <div className="flex gap-2">
          {canProcess && (
            <button
              onClick={() => processMutation.mutate()}
              disabled={processMutation.isPending}
              className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50"
            >
              {processMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Sparkles className="w-4 h-4" />
              )}
              Process Intake
            </button>
          )}
          {canConvert && (
            <button
              onClick={() => convertMutation.mutate()}
              disabled={convertMutation.isPending}
              className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-green-700 disabled:opacity-50"
            >
              {convertMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <ArrowRight className="w-4 h-4" />
              )}
              Convert to Project
            </button>
          )}
        </div>
      </div>

      {/* Duplicate Warning */}
      {intake.duplicate_of_id && (
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-6 flex items-center gap-3">
          <GitMerge className="w-5 h-5 text-orange-600" />
          <div>
            <p className="font-medium text-orange-800">Potential Duplicate Detected</p>
            <p className="text-sm text-orange-700">
              This appears to be a duplicate of intake #{intake.duplicate_of_id}
              ({Math.round((intake.duplicate_confidence || 0) * 100)}% confidence)
            </p>
          </div>
          <Link
            to={`/intake/${intake.duplicate_of_id}`}
            className="ml-auto text-orange-700 hover:text-orange-900 text-sm font-medium"
          >
            View Original
          </Link>
        </div>
      )}

      {/* Converted Notice */}
      {intake.converted_to_project_id && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6 flex items-center gap-3">
          <CheckCircle className="w-5 h-5 text-green-600" />
          <div>
            <p className="font-medium text-green-800">Converted to Project</p>
            <p className="text-sm text-green-700">
              This intake has been converted to a project
            </p>
          </div>
          <Link
            to={`/projects/${intake.converted_to_project_id}`}
            className="ml-auto text-green-700 hover:text-green-900 text-sm font-medium flex items-center gap-1"
          >
            View Project <ExternalLink className="w-4 h-4" />
          </Link>
        </div>
      )}

      <div className="grid grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="col-span-2 space-y-6">
          {/* PM Brief */}
          {intake.pm_brief ? (
            <PMBriefCard brief={intake.pm_brief} />
          ) : (
            <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
              <FileText className="w-12 h-12 mx-auto text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No PM Brief Yet</h3>
              <p className="text-gray-600 mb-4">
                Process this intake to extract a structured PM brief
              </p>
              {canProcess && (
                <button
                  onClick={() => processMutation.mutate()}
                  disabled={processMutation.isPending}
                  className="inline-flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-indigo-700"
                >
                  {processMutation.isPending ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Sparkles className="w-4 h-4" />
                  )}
                  Process Now
                </button>
              )}
            </div>
          )}

          {/* Raw Content */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Original Content</h3>
            <div className="bg-gray-50 rounded-lg p-4 font-mono text-sm whitespace-pre-wrap">
              {intake.raw_content}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Priority */}
          {intake.priority_score !== null && (
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h4 className="font-semibold text-gray-900 mb-2">Priority Score</h4>
              <div className="flex items-center gap-3">
                <div className={clsx(
                  'text-3xl font-bold',
                  intake.priority_score >= 70 ? 'text-red-600' :
                  intake.priority_score >= 40 ? 'text-orange-600' : 'text-green-600'
                )}>
                  {Math.round(intake.priority_score)}
                </div>
                <div className="text-sm text-gray-500">/ 100</div>
              </div>
              {intake.priority_rationale && (
                <p className="text-sm text-gray-600 mt-2">{intake.priority_rationale}</p>
              )}
            </div>
          )}

          {/* Clarifying Questions */}
          <QuestionsCard
            intakeId={Number(id)}
            questions={intake.clarifying_questions}
          />

          {/* Stakeholders */}
          {intake.stakeholders.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Users className="w-4 h-4" />
                Stakeholders
              </h4>
              <div className="space-y-2">
                {intake.stakeholders.map((s) => (
                  <div key={s.id} className="flex items-center justify-between text-sm">
                    <span className="font-medium">{s.name}</span>
                    <span className="text-gray-500">{s.role}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function PMBriefCard({ brief }: { brief: IntakeDetail['pm_brief'] }) {
  if (!brief) return null;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">PM Brief</h3>
        <div className="flex items-center gap-2 text-sm">
          <span className="text-gray-500">Extraction Confidence:</span>
          <span className={clsx(
            'font-medium',
            brief.extraction_confidence >= 0.7 ? 'text-green-600' :
            brief.extraction_confidence >= 0.4 ? 'text-yellow-600' : 'text-red-600'
          )}>
            {Math.round(brief.extraction_confidence * 100)}%
          </span>
        </div>
      </div>

      <div className="space-y-6">
        {/* Problem Statement */}
        {brief.problem_statement && (
          <Section title="Problem Statement" icon={<Target className="w-4 h-4" />}>
            <p className="text-gray-700">{brief.problem_statement}</p>
          </Section>
        )}

        {/* Target Users & Use Cases */}
        <div className="grid grid-cols-2 gap-4">
          {brief.target_users.length > 0 && (
            <Section title="Target Users" icon={<Users className="w-4 h-4" />}>
              <ul className="list-disc list-inside text-sm text-gray-700">
                {brief.target_users.map((u, i) => <li key={i}>{u}</li>)}
              </ul>
            </Section>
          )}
          {brief.use_cases.length > 0 && (
            <Section title="Use Cases">
              <ul className="list-disc list-inside text-sm text-gray-700">
                {brief.use_cases.map((u, i) => <li key={i}>{u}</li>)}
              </ul>
            </Section>
          )}
        </div>

        {/* Metrics */}
        {(brief.north_star_metric || brief.input_metrics.length > 0) && (
          <Section title="Success Metrics">
            {brief.north_star_metric && (
              <p className="text-sm mb-2">
                <span className="font-medium">North Star:</span> {brief.north_star_metric}
              </p>
            )}
            {brief.input_metrics.length > 0 && (
              <ul className="list-disc list-inside text-sm text-gray-700">
                {brief.input_metrics.map((m, i) => <li key={i}>{m}</li>)}
              </ul>
            )}
          </Section>
        )}

        {/* Constraints */}
        {(brief.security_constraints || brief.privacy_constraints || brief.performance_constraints) && (
          <Section title="Constraints" icon={<Shield className="w-4 h-4" />}>
            <div className="text-sm space-y-1">
              {brief.security_constraints && (
                <p><span className="font-medium">Security:</span> {brief.security_constraints}</p>
              )}
              {brief.privacy_constraints && (
                <p><span className="font-medium">Privacy:</span> {brief.privacy_constraints}</p>
              )}
              {brief.performance_constraints && (
                <p><span className="font-medium">Performance:</span> {brief.performance_constraints}</p>
              )}
            </div>
          </Section>
        )}

        {/* Acceptance Criteria */}
        {brief.acceptance_criteria.length > 0 && (
          <Section title="Acceptance Criteria">
            <ul className="space-y-1">
              {brief.acceptance_criteria.map((c, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>{c}</span>
                </li>
              ))}
            </ul>
          </Section>
        )}

        {/* Dependencies */}
        {(brief.team_dependencies.length > 0 || brief.service_dependencies.length > 0) && (
          <Section title="Dependencies">
            <div className="grid grid-cols-2 gap-4 text-sm">
              {brief.team_dependencies.length > 0 && (
                <div>
                  <p className="font-medium mb-1">Teams</p>
                  <ul className="list-disc list-inside text-gray-700">
                    {brief.team_dependencies.map((d, i) => <li key={i}>{d}</li>)}
                  </ul>
                </div>
              )}
              {brief.service_dependencies.length > 0 && (
                <div>
                  <p className="font-medium mb-1">Services</p>
                  <ul className="list-disc list-inside text-gray-700">
                    {brief.service_dependencies.map((d, i) => <li key={i}>{d}</li>)}
                  </ul>
                </div>
              )}
            </div>
          </Section>
        )}

        {/* Missing Fields Warning */}
        {brief.missing_fields.length > 0 && (
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <div className="flex items-center gap-2 text-orange-800 font-medium mb-2">
              <AlertCircle className="w-4 h-4" />
              Missing Information
            </div>
            <ul className="list-disc list-inside text-sm text-orange-700">
              {brief.missing_fields.map((f, i) => (
                <li key={i}>{f.replace(/_/g, ' ')}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

function Section({ title, icon, children }: {
  title: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div>
      <h4 className="flex items-center gap-2 font-medium text-gray-900 mb-2">
        {icon}
        {title}
      </h4>
      {children}
    </div>
  );
}

function QuestionsCard({ intakeId, questions }: {
  intakeId: number;
  questions: ClarifyingQuestion[];
}) {
  const queryClient = useQueryClient();
  const [answeringId, setAnsweringId] = useState<number | null>(null);
  const [answerText, setAnswerText] = useState('');

  const answerMutation = useMutation({
    mutationFn: ({ questionId, answer }: { questionId: number; answer: string }) =>
      answerQuestion(intakeId, questionId, answer),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intake', String(intakeId)] });
      setAnsweringId(null);
      setAnswerText('');
    },
  });

  const blockingCount = questions.filter(q => q.is_blocking && !q.is_answered).length;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
        <MessageSquare className="w-4 h-4" />
        Clarifying Questions
        {blockingCount > 0 && (
          <span className="bg-red-100 text-red-700 text-xs px-2 py-0.5 rounded-full">
            {blockingCount} blocking
          </span>
        )}
      </h4>

      {questions.length === 0 ? (
        <p className="text-sm text-gray-500">No questions generated yet</p>
      ) : (
        <div className="space-y-4">
          {questions.map((q) => (
            <div key={q.id} className={clsx(
              'border rounded-lg p-3',
              q.is_blocking && !q.is_answered ? 'border-red-200 bg-red-50' : 'border-gray-200'
            )}>
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-medium text-gray-900">{q.question}</p>
                {q.is_answered ? (
                  <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                ) : q.is_blocking ? (
                  <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
                ) : null}
              </div>

              {q.context && (
                <p className="text-xs text-gray-500 mt-1">{q.context}</p>
              )}

              {q.is_answered && q.answer ? (
                <div className="mt-2 bg-green-50 rounded p-2">
                  <p className="text-sm text-green-800">{q.answer}</p>
                </div>
              ) : answeringId === q.id ? (
                <div className="mt-2 space-y-2">
                  <textarea
                    value={answerText}
                    onChange={(e) => setAnswerText(e.target.value)}
                    placeholder="Type your answer..."
                    className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                    rows={2}
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={() => answerMutation.mutate({ questionId: q.id, answer: answerText })}
                      disabled={!answerText.trim() || answerMutation.isPending}
                      className="text-xs bg-indigo-600 text-white px-2 py-1 rounded disabled:opacity-50"
                    >
                      Submit
                    </button>
                    <button
                      onClick={() => { setAnsweringId(null); setAnswerText(''); }}
                      className="text-xs text-gray-600 hover:text-gray-900"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => setAnsweringId(q.id)}
                  className="text-xs text-indigo-600 hover:text-indigo-800 mt-2"
                >
                  Answer this question
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
