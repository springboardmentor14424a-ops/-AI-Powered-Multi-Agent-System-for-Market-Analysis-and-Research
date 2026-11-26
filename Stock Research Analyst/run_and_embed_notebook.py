import os
import sys
import io
import base64
import nbformat
from nbformat.v4 import new_output
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def execute_notebook(nb_path, cwd='.'):
    print(f"\n==========================================")
    print(f"Executing: {nb_path} (working dir: {cwd})")
    print(f"==========================================")
    
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)
        
    old_cwd = os.getcwd()
    os.chdir(cwd)
    
    # Shared execution namespace
    glob_ns = {
        '__name__': '__main__',
        '__file__': os.path.abspath(nb_path),
    }
    
    exec_count = 1
    for i, cell in enumerate(nb.cells):
        if cell.cell_type != 'code':
            continue
            
        print(f"\n--- Running Cell {i+1} ---")
        code = cell.source
        
        # We intercept plt.show to capture figures
        captured_figs = []
        original_show = plt.show
        def custom_show(*args, **kwargs):
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=130)
            buf.seek(0)
            b64_data = base64.b64encode(buf.read()).decode('utf-8')
            captured_figs.append(b64_data)
            plt.close('all')
        plt.show = custom_show
        
        # Capture stdout
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        redirected_output = io.StringIO()
        sys.stdout = redirected_output
        sys.stderr = redirected_output
        
        cell.outputs = []
        error_occurred = False
        
        try:
            exec(code, glob_ns)
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            error_occurred = True
            print(tb)
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            plt.show = original_show
            
        out_text = redirected_output.getvalue()
        if out_text:
            print(out_text, end='')
            cell.outputs.append(new_output(
                output_type='stream',
                name='stdout',
                text=out_text
            ))
            
        for fig_b64 in captured_figs:
            cell.outputs.append(new_output(
                output_type='display_data',
                data={
                    'image/png': fig_b64,
                    'text/plain': '<Figure size ...>'
                }
            ))
            print(f"  ✓ Captured and embedded plot ({len(fig_b64)} bytes base64)")
            
        cell.execution_count = exec_count
        exec_count += 1
        
        if error_occurred:
            print(f"❌ Error occurred in cell {i+1}")
            break
            
    os.chdir(old_cwd)
    
    with open(nb_path, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f)
        
    print(f"\n✅ Finished execution and saved outputs for {nb_path}!")

if __name__ == '__main__':
    execute_notebook(os.path.join('notebooks', '02_features_analysis.ipynb'), cwd='notebooks')
