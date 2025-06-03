import sqlite3
import getpass

def generate_number_call(self, row):
        user = getpass.getuser().capitalize()
        """Generates and assigns a number in the format K-{zakazka.number}-{unique_number}."""
        zakazka_index = self.polozka_filter_model.index(row, 4)  # Get zakazka column (foreign key)
        polozka_id_index = self.polozka_filter_model.index(row, 0)  # Get polozka ID column

        zakazka_id = self.polozka_filter_model.data(zakazka_index)
        polozka_id = self.polozka_filter_model.data(polozka_id_index)

        if zakazka_id is None or polozka_id is None:
            return

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        # Get zakázka number using zakazka_id
        cursor.execute("SELECT number FROM zakázka WHERE title = ?", (zakazka_id,))
        zakazka_number = cursor.fetchone()

        if zakazka_number is None:
            conn.close()
            return

        zakazka_number = zakazka_number[0]  # Extract the actual number from the tuple

        # Get the highest existing number assigned for this zakázka
        cursor.execute("SELECT vykres FROM položka WHERE zakazka = ? AND vykres LIKE ?", 
                    (zakazka_id, f"K-{zakazka_number}-%"))
        existing_numbers = cursor.fetchall()

        # Find the next available vykres number
        next_number = 1
        if existing_numbers:
            existing_numbers = [int(num[0].split('-')[-1]) for num in existing_numbers if num[0] and num[0].startswith(f"K-{zakazka_number}-")]
            if existing_numbers:
                next_number = max(existing_numbers) + 1

        generated_number = f"K-{zakazka_number}-{next_number:02d}"

        # Update the database
        cursor.execute("UPDATE položka SET vykres = ? WHERE id = ? WHERE user=? AND (vykres IS NULL OR vykres = '')", 
                    (generated_number, polozka_id, user))
        conn.commit()
        conn.close()

        # Refresh model
        self.polozka_model.select()
