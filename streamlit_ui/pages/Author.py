"""
Author page for Trading System.
Personal information about the developer/author
"""

import os
import sys

import pandas as pd
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


def load_custom_css():
    """Load custom CSS from file and configuration"""
    css_file = os.path.join(os.path.dirname(__file__), "..", "styles.css")
    try:
        with open(css_file, "r") as f:
            css_content = f.read()

        # Add CSS variables from configuration
        from css_config import generate_css_variables, get_theme_css
        css_variables = generate_css_variables()
        theme_css = get_theme_css()

        # Combine all CSS
        full_css = css_variables + css_content + theme_css
        st.markdown(f"<style>{full_css}</style>", unsafe_allow_html=True)

    except FileNotFoundError:
        st.warning("Custom CSS file not found. Using default styling.")
    except Exception as e:
        st.error(f"Error loading custom CSS: {e}")


def author_page():
    """Author page with personal information"""

    # ============================================
    # CUSTOMIZE THIS SECTION - Personal Introduction
    # ============================================
    st.title("👨‍💻 About Me")

    # Hero section with name and tagline
    col1, col2 = st.columns([1, 2])

    with col1:
        # You can add a profile image here if you have one
        # st.image("path/to/your/profile_image.jpg", width=200)
        st.markdown("### Nishant Nayar")
        st.caption("📌 Vice President - Lead Solution Analyst")

    with col2:
        st.markdown("""
        **Welcome!** 👋
        
        Nishant is a passionate data management professional with a proven track record of developing and executing 
        strategic initiatives within Investment Bank, Commercial Bank and Asset Management segments of the financial 
        services. He excels at translating complex data challenges into actionable solutions by leveraging data 
        governance best practices and applied data science techniques. Additionally, he is a critical thinker and a 
        problem solver, bringing a strong work ethic and a commitment to data-driven decision making.
        """)

    st.divider()

    # ============================================
    # CUSTOMIZE THIS SECTION - Bio & Background
    # ============================================
    st.subheader("📖 My Story")

    st.markdown("""
    Tell your story here. You might want to include:
    - Your background and how you got into programming/trading
    - What inspired you to build this trading system
    - Your journey in learning and development
    - Key milestones or achievements
    - What you're currently working on or learning
    """)

    st.divider()

    # ============================================
    # CUSTOMIZE THIS SECTION - Technical Skills
    # ============================================
    st.subheader("🛠️ Technical Skills")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **Languages:**
        - [Language 1]
        - [Language 2]
        - [Language 3]
        - [Add more...]
        """)

    with col2:
        st.markdown("""
        **Frameworks & Tools:**
        - [Framework 1]
        - [Framework 2]
        - [Tool 1]
        - [Add more...]
        """)

    with col3:
        st.markdown("""
        **Specializations:**
        - [Specialization 1]
        - [Specialization 2]
        - [Specialization 3]
        - [Add more...]
        """)

    st.divider()

    # ============================================
    # CUSTOMIZE THIS SECTION - This Project
    # ============================================
    st.subheader("🚀 About This Trading System")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **What I Built:**
        - 📈 [Feature 1 - e.g., Real-time market data integration]
        - 🔍 [Feature 2 - e.g., Advanced technical analysis]
        - 📊 [Feature 3 - e.g., Portfolio tracking]
        - ⚡ [Feature 4 - e.g., Automated strategies]
        - 🛡️ [Feature 5 - e.g., Risk management]
        - 📱 [Feature 6 - e.g., Modern web interface]
        """)

    with col2:
        st.markdown("""
        **Tech Stack Used:**
        - Python 3.9+
        - FastAPI (Backend API)
        - Streamlit (Frontend UI)
        - PostgreSQL (Database)
        - Redis (Caching)
        - [Add other technologies you used]
        """)

    st.markdown("""
    **Why I Built This:**
    
    [Explain your motivation for building this trading system. 
    What problem were you trying to solve? 
    What did you learn along the way?]
    """)

    st.divider()

    # ============================================
    # CUSTOMIZE THIS SECTION - Experience & Education
    # ============================================
    st.subheader("🎓 Experience & Education")

    experience_data = {
        "Role/Position": [
            "[Role 1 - e.g., Software Engineer]",
            "[Role 2 - e.g., Data Analyst]",
            "[Role 3 - e.g., Student/Intern]"
        ],
        "Company/Institution": [
            "[Company/University 1]",
            "[Company/University 2]",
            "[Company/University 3]"
        ],
        "Duration": [
            "[Date Range 1]",
            "[Date Range 2]",
            "[Date Range 3]"
        ],
        "Key Achievements": [
            "[Achievement 1]",
            "[Achievement 2]",
            "[Achievement 3]"
        ]
    }

    df_experience = pd.DataFrame(experience_data)
    st.dataframe(df_experience, width='stretch', hide_index=True)

    st.divider()

    # ============================================
    # CUSTOMIZE THIS SECTION - Projects & Achievements
    # ============================================
    st.subheader("🏆 Projects & Achievements")

    st.markdown("""
    **Notable Projects:**
    - **[Project Name 1]**: [Brief description]
    - **[Project Name 2]**: [Brief description]
    - **[Project Name 3]**: [Brief description]
    
    **Achievements:**
    - [Achievement 1 - e.g., Certifications, Awards, Publications]
    - [Achievement 2]
    - [Achievement 3]
    """)

    st.divider()

    # ============================================
    # CUSTOMIZE THIS SECTION - Interests & Hobbies
    # ============================================
    st.subheader("🎯 Interests & Hobbies")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Professional Interests:**
        - [Interest 1 - e.g., Algorithmic Trading]
        - [Interest 2 - e.g., Machine Learning]
        - [Interest 3 - e.g., Financial Modeling]
        - [Add more...]
        """)

    with col2:
        st.markdown("""
        **Personal Hobbies:**
        - [Hobby 1 - e.g., Reading]
        - [Hobby 2 - e.g., Hiking]
        - [Hobby 3 - e.g., Photography]
        - [Add more...]
        """)

    st.divider()

    # ============================================
    # CUSTOMIZE THIS SECTION - Contact & Links
    # ============================================
    st.subheader("📬 Connect With Me")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Contact Information:**
        - 📧 Email: nishant.nayar@hotmail.com
        - 📍 Location: Greater Chicago Area
        """)

    with col2:
        st.markdown("""
        **Social & Professional Links:**
        - 💼 LinkedIn: [nishantnayar](https://www.linkedin.com/in/nishantnayar/)
        - 🐙 GitHub: [nishantnayar](https://github.com/nishantnayar)
        - 📝 Medium: [@nishant-nayar](https://medium.com/@nishant-nayar)
        """)

    st.divider()

    # ============================================
    # CUSTOMIZE THIS SECTION - Fun Facts
    # ============================================
    st.subheader("✨ Fun Facts About Me")

    st.markdown("""
    - [Fun fact 1 - e.g., I've been coding since I was 12]
    - [Fun fact 2 - e.g., I love solving complex problems]
    - [Fun fact 3 - e.g., I'm passionate about financial markets]
    - [Fun fact 4 - e.g., I enjoy contributing to open source]
    - [Add more fun facts...]
    """)

    st.divider()

    # ============================================
    # CUSTOMIZE THIS SECTION - Current Focus
    # ============================================
    st.subheader("🎯 What I'm Working On Now")

    st.markdown("""
    **Current Projects:**
    - [Project 1 you're currently working on]
    - [Project 2 you're currently working on]
    
    **Learning:**
    - Kaggle’s 5-Day AI Agents Intensive Course
    - Quantum Computing
    
    **Goals:**
    - [Short-term goal]
    - [Long-term goal]
    """)

    # Optional: Add a call-to-action
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 20px;'>
        <h4>💡 Let's Connect!</h4>
        <p>Feel free to reach out if you'd like to collaborate, discuss trading systems, or just say hello!</p>
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main function for Author page"""
    load_custom_css()
    author_page()


if __name__ == "__main__":
    main()
