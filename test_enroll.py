import redis
import pandas as pd

# Connect to Redis Client
hostname = 'redis-19487.c8.us-east-1-4.ec2.redns.redis-cloud.com'
portnumber = 19487
password = 'ee3x3qAQ7yPMws3P5vHquvbE8o6LY84d'

r = redis.StrictRedis(host=hostname,
                     port=portnumber,
                     password=password)

def list_registered_users():
    """
    Retrieve and display all registered users from Redis database
    """
    print("\n=== REGISTERED USERS ===")
    # Get all keys from register
    all_keys = r.hkeys('academy:register')
    
    # Convert bytes to strings and print
    if not all_keys:
        print("No registered users found")
        return []
    
    registered_users = [key.decode('utf-8') for key in all_keys]
    
    # Format and display users
    user_data = []
    for i, user in enumerate(registered_users):
        parts = user.split('@')
        if len(parts) == 3:
            print(f"{i+1}. {parts[0]} ({parts[1]}) - {parts[2]}")
            user_data.append({
                "Name": parts[0],
                "Role": parts[1],
                "Subject": parts[2],
                "Key": user
            })
        elif len(parts) == 2:
            print(f"{i+1}. {parts[0]} ({parts[1]})")
            user_data.append({
                "Name": parts[0],
                "Role": parts[1],
                "Subject": "Not Enrolled",
                "Key": user
            })
        else:
            print(f"{i+1}. {user}")
            user_data.append({
                "Name": user,
                "Role": "Unknown",
                "Subject": "Unknown",
                "Key": user
            })
    
    return user_data

def unenroll_user(user_key):
    """
    Unenroll a user from the system by key
    """
    try:
        # Check if key exists before deleting
        if r.hexists('academy:register', user_key):
            # Delete the user from Redis
            result = r.hdel('academy:register', user_key)
            if result == 1:
                print(f"\nSuccessfully unenrolled user: {user_key}")
                return True
            else:
                print(f"\nFailed to unenroll user: {user_key}")
                return False
        else:
            print(f"\nUser not found: {user_key}")
            return False
    except Exception as e:
        print(f"\nError occurred during unenrollment: {e}")
        return False

# Main test function
def test_unenroll_functionality():
    print("TESTING UNENROLL FUNCTIONALITY")
    print("==============================")
    
    # Step 1: List all users before unenrollment
    print("\nBEFORE UNENROLLMENT:")
    users = list_registered_users()
    
    if not users:
        print("\nNo users to unenroll. Test cannot proceed.")
        return
    
    # Create DataFrame for better visualization
    df = pd.DataFrame(users)
    print("\nUsers as DataFrame:")
    print(df)
    
    # Step 2: Select a user to unenroll (for testing, we'll use the first user)
    test_user = users[0]["Key"]
    user_name = users[0]["Name"]
    print(f"\nAttempting to unenroll user: {user_name} (Key: {test_user})")
    
    # Step 3: Perform the unenrollment
    success = unenroll_user(test_user)
    
    # Step 4: List all users after unenrollment
    print("\nAFTER UNENROLLMENT:")
    remaining_users = list_registered_users()
    
    # Step 5: Verify the user was removed
    if success:
        keys_after = [user["Key"] for user in remaining_users]
        if test_user not in keys_after:
            print(f"\nTEST PASSED: User {user_name} was successfully removed from the system")
        else:
            print(f"\nTEST FAILED: User {user_name} still exists in the system despite successful deletion response")
    else:
        print("\nTEST FAILED: Unenrollment operation was not successful")

# Run the test
if __name__ == "__main__":
    test_unenroll_functionality()