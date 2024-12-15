from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import pymysql

app = Flask(__name__)

# Database connection function using PyMySQL
def connect_to_db():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='Prasad04.',
        database='ftodo',
        cursorclass=pymysql.cursors.DictCursor
    )


@app.route('/upcoming')
def upcoming_tasks():
    try:
        connection = connect_to_db()
        with connection.cursor() as cursor:
            # Fetch tasks with specific repeat options (Weekly, Monthly, Yearly)
            cursor.execute("""
                SELECT task, notes, due_date, repeat_option 
                FROM tasks 
                WHERE repeat_option IN ('Weekly', 'Monthly', 'Yearly') 
                ORDER BY due_date ASC
            """)
            upcoming_tasks = cursor.fetchall()
    except Exception as e:
        print(f"Error fetching upcoming tasks: {e}")
        upcoming_tasks = []  # Default to an empty list in case of an error
    finally:
        connection.close()

    return render_template('upcoming.html', upcoming_tasks=upcoming_tasks)


@app.route('/')
def index():
    try:
        connection = connect_to_db()
        with connection.cursor() as cursor:
            # Fetch pending and completed tasks separately
            cursor.execute("SELECT * FROM tasks WHERE completed = FALSE ORDER BY created_at DESC")
            pending_tasks = cursor.fetchall()

            cursor.execute("SELECT * FROM tasks WHERE completed = TRUE ORDER BY completed_at DESC")
            completed_tasks = cursor.fetchall()
    except Exception as e:
        print(f"Error fetching tasks: {e}")
        pending_tasks, completed_tasks = [], []  # Return empty lists if an error occurs
    finally:
        connection.close()
    return render_template('index.html', pending_tasks=pending_tasks, completed_tasks=completed_tasks)
@app.route('/search', methods=['GET'])
def search_tasks():
    query = request.args.get('query', '').strip()
    tasks = []

    if query:
        try:
            connection = connect_to_db()
            with connection.cursor() as cursor:
                # Check if the query is a valid date
                is_date = False
                try:
                    # Attempt to parse the input as a date
                    datetime.strptime(query, '%Y-%m-%d')
                    is_date = True
                except ValueError:
                    pass  # Not a valid date, proceed to search as text

                # Adjust SQL query based on input type
                if is_date:
                    cursor.execute("""
                        SELECT * FROM tasks
                        WHERE due_date = %s
                    """, (query,))
                else:
                    cursor.execute("""
                        SELECT * FROM tasks
                        WHERE task LIKE %s
                    """, (f"%{query}%",))

                tasks = cursor.fetchall()
        except Exception as e:
            print(f"Error searching tasks: {e}")
        finally:
            connection.close()

    return render_template('search_results.html', query=query, tasks=tasks)
@app.route('/add', methods=['POST'])
def add_task():
    task = request.form.get('task')
    notes = request.form.get('notes')  # Retrieve notes from the form
    due_date = request.form.get('due_date')  # Retrieve due date from the form
    repeat_option = request.form.get('repeat_option')  # Retrieve repeat option from the form
    if task:
        try:
            connection = connect_to_db()
            with connection.cursor() as cursor:
                created_at = datetime.now()
                cursor.execute(
                    """
                    INSERT INTO tasks (task, notes, due_date, `repeat_option`, created_at) 
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (task, notes, due_date, repeat_option, created_at)
                )

                connection.commit()
        except Exception as e:
            print(f"Error adding task: {e}")
        finally:
            connection.close()
    return redirect(url_for('index'))
@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    try:
        connection = connect_to_db()
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            connection.commit()
    except Exception as e:
        print(f"Error deleting task: {e}")
    finally:
        connection.close()
    return redirect(url_for('index'))

@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    try:
        connection = connect_to_db()
        with connection.cursor() as cursor:
            completed_at = datetime.now()
            cursor.execute(
                "UPDATE tasks SET completed = TRUE, completed_at = %s WHERE id = %s",
                (completed_at, task_id)
            )
            connection.commit()
    except Exception as e:
        print(f"Error completing task: {e}")
    finally:
        connection.close()
    return redirect(url_for('index'))
@app.route('/analysis')
def analysis():
    try:
        connection = connect_to_db()
        with connection.cursor() as cursor:
            # Query to count the tasks grouped by repeat_option
            cursor.execute("""
                SELECT repeat_option, COUNT(*) as count 
                FROM tasks 
                GROUP BY repeat_option
            """)
            repeat_counts = cursor.fetchall()
    except Exception as e:
        print(f"Error fetching analysis data: {e}")
        repeat_counts = []  # If an error occurs, set the result to an empty list
    finally:
        connection.close()

    # Prepare data for the pie chart
    repeat_options = ['None', 'Daily', 'Weekly', 'Monthly', 'Yearly']
    counts = {option: 0 for option in repeat_options}
    for row in repeat_counts:
        counts[row['repeat_option']] = row['count']

    # Return the analysis template with the data
    return render_template('analysis.html', counts=counts)
@app.route('/calendar')
def calendar():
    try:
        connection = connect_to_db()
        with connection.cursor() as cursor:
            # Fetch tasks with due dates
            cursor.execute("SELECT id, task, due_date FROM tasks WHERE due_date IS NOT NULL")
            tasks = cursor.fetchall()
    except Exception as e:
        print(f"Error fetching calendar data: {e}")
        tasks = []  # Default to an empty list if there's an error
    finally:
        connection.close()
    return render_template('calendar.html', tasks=tasks)

if __name__ == '__main__':
    app.run(debug=True)
