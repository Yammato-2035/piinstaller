import React, { useEffect, useState } from 'react';
import { fetchOperatorStatus } from './rescueOperatorApi';
import { isRescueOperatorMode } from './rescueOperatorMode';
import { getRescueDict, tPath, type RescueLocale } from './rescueLocale';

type CheckItem = { id: string; label: string; hint?: string; status: string };
type Section = { id: string; title: string; items: CheckItem[] };

export const RescueOperatorChecklistPanel: React.FC<{ locale?: RescueLocale }> = ({ locale = 'de' }) => {
  const enabled = isRescueOperatorMode();
  const dict = getRescueDict(locale);
  const [sections, setSections] = useState<Section[]>([]);
  const [preflight, setPreflight] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    if (!enabled) return;
    fetchOperatorStatus()
      .then((data) => {
        const cl = data.checklist as { sections?: Section[] } | null;
        setSections(cl?.sections || []);
        setPreflight((data.preflight as Record<string, unknown>) || null);
      })
      .catch(() => undefined);
  }, [enabled]);

  if (!enabled) return null;

  return (
    <section
      className="rescue-operator-checklist"
      style={{
        background: 'rgba(30,58,95,0.9)',
        border: '1px solid #475569',
        borderRadius: 10,
        padding: 12,
        marginBottom: 16,
        fontSize: 14,
      }}
      data-rescue-operator-checklist="true"
    >
      <h3 style={{ margin: '0 0 8px', color: '#96c93d' }}>{tPath(dict, 'operatorChecklist.title')}</h3>
      {preflight ? (
        <pre style={{ fontSize: 11, overflow: 'auto', margin: '0 0 8px' }}>{JSON.stringify(preflight, null, 2)}</pre>
      ) : null}
      {sections.map((sec) => (
        <div key={sec.id} style={{ marginBottom: 8 }}>
          <strong>{sec.title}</strong>
          <ul style={{ margin: '4px 0 0', paddingLeft: 18 }}>
            {sec.items.map((item) => (
              <li key={item.id}>
                {item.label} — {item.status}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </section>
  );
};
