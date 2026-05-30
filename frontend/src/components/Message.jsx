export default function Message({ msg }) {
  if (msg.type === "user") {
    return (
      <div className="self-end bg-emerald-600 text-white px-4 py-2 rounded-xl max-w-sm text-sm">
        {msg.text}
      </div>
    )
  }

  if (msg.type === "error") {
    return <div className="text-red-400 text-sm">{msg.text}</div>
  }

  const { data } = msg

  return (
    <div className="bg-gray-800 rounded-xl p-4 text-sm flex flex-col gap-3">

      {/* Sources */}
      <div className="flex gap-2 flex-wrap">
        {data.sources_used?.map(s => (
          <span key={s} className="bg-emerald-900 text-emerald-300 px-2 py-1 rounded text-xs">
            {s}
          </span>
        ))}
      </div>

      {/* AI Summary */}
      {data.summary && (
        <div className="bg-gray-700 border border-emerald-800 rounded-lg px-4 py-3">
          <p className="text-xs text-emerald-400 mb-1">AI Summary</p>
          <p className="text-gray-200 text-sm leading-relaxed">{data.summary}</p>
        </div>
      )}

      {/* Incidents */}
      {data.incidents?.length > 0 && (
        <div>
          <p className="text-gray-400 text-xs mb-2">Related Incidents</p>
          <div className="flex flex-col gap-2">
            {data.incidents.map((inc, i) => (
              <div key={i} className="bg-gray-900 border border-red-900 rounded-lg px-3 py-2 text-xs">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-red-400 font-semibold">{inc.id}</span>
                  <span className={
                    inc.severity === "high" ? "bg-red-900 text-red-300 px-2 py-0.5 rounded" :
                    inc.severity === "medium" ? "bg-yellow-900 text-yellow-300 px-2 py-0.5 rounded" :
                    "bg-gray-700 text-gray-300 px-2 py-0.5 rounded"
                  }>
                    {inc.severity}
                  </span>
                </div>
                <p className="text-white">{inc.description}</p>
                <div className="flex justify-between mt-1 text-gray-400">
                  <span>service: {inc.service}</span>
                  <span>issue #{inc.issue_number}</span>
                  <span className={
                    inc.status === "open" ? "text-red-400" :
                    inc.status === "investigating" ? "text-yellow-400" :
                    "text-green-400"
                  }>{inc.status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* GitHub Data */}
      {data.correlated_data?.length > 0 && !data.correlated_data[0]?.login && (
        <div>
          <p className="text-gray-400 text-xs mb-1">GitHub Data</p>
          <div className="flex flex-col gap-1">
            {data.correlated_data.map((row, i) => (
              <div key={i} className="bg-gray-700 rounded px-3 py-2 text-xs">
                <span className="text-emerald-400">#{row.number}</span>{" "}
                <span className="text-white">{row.title}</span>{" "}
                {row.state && (
                  <span className={row.state === "open" ? "text-yellow-400" : "text-gray-400"}>
                    [{row.state}]
                  </span>
                )}
                {row.merged_at && (
                  <span className="text-green-400"> [merged]</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Contributors */}
      {data.correlated_data?.length > 0 && data.correlated_data[0]?.login && (
        <div>
          <p className="text-gray-400 text-xs mb-1">Top Contributors</p>
          <div className="flex flex-col gap-1">
            {data.correlated_data.map((row, i) => (
              <div key={i} className="bg-gray-700 rounded px-3 py-2 text-xs flex justify-between">
                <span className="text-emerald-400">@{row.login}</span>
                <span className="text-gray-300">{row.contributions} commits</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Open Issues */}
      {data.open_issues?.length > 0 && (
        <div>
          <p className="text-gray-400 text-xs mb-1">Supporting Data</p>
          <div className="flex flex-col gap-1">
            {data.open_issues.map((row, i) => (
              <div key={i} className="bg-gray-700 rounded px-3 py-2 text-xs">
                <span className="text-emerald-400">#{row.number}</span>{" "}
                <span className="text-white">{row.title}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SQL Queries */}
      <details className="text-xs">
        <summary className="text-gray-500 cursor-pointer">View SQL queries</summary>
        {data.sql_queries?.map((q, i) => (
          <pre key={i} className="bg-gray-900 text-emerald-300 p-2 rounded mt-1 overflow-x-auto whitespace-pre-wrap">
            {q}
          </pre>
        ))}
      </details>

    </div>
  )
}