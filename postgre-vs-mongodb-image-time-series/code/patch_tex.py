import re

with open("../paper/icct_alfa_yohannis_2.tex", "r") as f:
    text = f.read()

perf_table = r'''\begin{table}[htbp]
\centering
\renewcommand{\arraystretch}{1.1}
\caption{Insert Throughput and Binary Payload Retrieval Latency (100 rows)}
\label{tab:performance_summary}
\begin{tabular}{l r r r r}
\hline
\textbf{Res.} & \multicolumn{2}{c}{\textbf{Insert (rows/s)}} & \multicolumn{2}{c}{\textbf{Retrieval (ms)}} \\
 & \textbf{PostgreSQL} & \textbf{MongoDB} & \textbf{PostgreSQL} & \textbf{MongoDB} \\
\hline
1080p & 22.0  & \textbf{133.2} & 1587   & \textbf{259}   \\
1440p & 19.1  & \textbf{21.3}  & 2284   & \textbf{638}   \\
4K    & \textbf{8.4}   & 4.6   & 2788   & \textbf{1842}  \\
5K    & \textbf{4.6}   & 2.2   & 5461   & \textbf{2619}  \\
6K    & \textbf{4.1}   & Fail  & \textbf{8219}   & Fail  \\
\hline
\end{tabular}
\end{table}'''
perf_table = perf_table.replace('\\', '\\\\')

storage_table = r'''\begin{table}[htbp]
\centering
\renewcommand{\arraystretch}{1.1}
\caption{Storage Amplification and Disk Usage (100 rows)}
\label{tab:storage_summary}
\begin{tabular}{l r r r r}
\hline
\textbf{Res.} & \textbf{PostgreSQL} & \textbf{MongoDB} & \textbf{PostgreSQL} & \textbf{MongoDB} \\
 & \textbf{Disk (MB)} & \textbf{Disk (MB)} & \textbf{Amp} & \textbf{Amp} \\
\hline
1080p & 112.8  & 13.6   & 1.04$\times$ & \textbf{0.12$\times$} \\
1440p & 172.7  & 128.1  & 1.05$\times$ & \textbf{0.78$\times$} \\
4K    & \textbf{319.3}  & 922.7  & \textbf{1.06$\times$} & 3.08$\times$ \\
5K    & \textbf{501.8} & 1473.2 & \textbf{1.04$\times$} & 3.05$\times$ \\
6K    & \textbf{670.1} & Fail   & \textbf{1.04$\times$} & Fail \\
\hline
\end{tabular}
\end{table}'''
storage_table = storage_table.replace('\\', '\\\\')

# Replace table 1
text = re.sub(r'\\begin{table}\[htbp\]\n\\centering\n\\renewcommand{\\arraystretch}{1\.1}\n\\caption{Insert Throughput.*?\\end{table}', perf_table, text, flags=re.DOTALL)

# Replace table 2
text = re.sub(r'\\begin{table}\[htbp\]\n\\centering\n\\renewcommand{\\arraystretch}{1\.1}\n\\caption{Storage Amplification.*?\\end{table}', storage_table, text, flags=re.DOTALL)

# Remove table 3
text = re.sub(r'\\begin{table}\[htbp\]\n\\centering\n\\renewcommand{\\arraystretch}{1\.1}\n\\caption{Binary Payload Retrieval.*?\\end{table}', '', text, flags=re.DOTALL)

# Update textual references
text = text.replace('Tables~\\ref{tab:scaling_summary}--\\ref{tab:retrieval_summary}', 'Tables~\\ref{tab:performance_summary} and~\\ref{tab:storage_summary}')
text = text.replace('Table~\\ref{tab:scaling_summary}', 'Table~\\ref{tab:performance_summary}')
text = text.replace('Table~\\ref{tab:retrieval_summary}', 'Table~\\ref{tab:performance_summary}')

# Fix the body text numbers to map reality (100 rows instead of 250 rows).
text = text.replace('1080p, MongoDB achieves 65 rows/s---$3.7\\times$ faster than PostgreSQL\'s 17 rows/s',
                    '1080p, MongoDB achieves 133.2 rows/s---$6\\times$ faster than PostgreSQL\'s 22.0 rows/s')

text = text.replace('parity (15.6 vs.\ 11.3 rows/s)', 'parity (21.3 vs.\ 19.1 rows/s)')
text = text.replace('achieves 5.8 rows/s against MongoDB\'s 4.3 rows/s', 'achieves 8.4 rows/s against MongoDB\'s 4.6 rows/s')
text = text.replace('provides 3.8 rows/s against MongoDB\'s 2.2 rows/s', 'provides 4.6 rows/s against MongoDB\'s 2.2 rows/s')
text = text.replace('3970~ms', '1587~ms')
text = text.replace('1250~ms', '259~ms')
text = text.replace('$5.8$~s vs $11.3$~s', '$1.8$~s vs $2.8$~s')
text = text.replace('in 24~s', 'in 8.2~s')

with open("../paper/icct_alfa_yohannis_2.tex", "w") as f:
    f.write(text)
print("Updated tex successfully.")
